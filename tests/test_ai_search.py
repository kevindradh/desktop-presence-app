import numpy as np
import pytest
from sqlalchemy import select
from ai.embedding.search import identify
from app.models.entities import FaceEmbedding
from app.repositories.core import EmbeddingRepository,MemberRepository
from tests.test_database import store,graph

pytestmark=pytest.mark.database


def test_single_exact_result_matches_grouped_search_with_duplicate_angles_and_ties(store):
    from app.models.entities import FaceAngle
    one=np.zeros(512);one[0]=1
    other=np.zeros(512);other[1]=1
    with store.db.transaction() as session:
        group,first,_,_=graph(session)
        second=MemberRepository(session).create('TIE-2','Second',group.id,'synthetic/none.png')
        repo=EmbeddingRepository(session)
        for angle in FaceAngle:repo.create(first.id,one,angle,'tie-model')
        repo.create(second.id,one,'FRONT','tie-model')
        repo.create(second.id,other,'LEFT','tie-model')
        first_id,second_id=first.id,second.id
    with store.db.transaction() as session:
        repo=EmbeddingRepository(session)
        for probe,expected in ((one,first_id),(other,second_id),(-one,second_id)):
            single=repo.nearest(probe,model_version='tie-model',limit=1)
            grouped=repo.nearest(probe,model_version='tie-model',limit=5)
            assert single[0]==grouped[0] and single[0].member_id==expected
        assert len(repo.nearest(one,model_version='tie-model',limit=5))==2


def test_search_storage_upgrade_rewrites_existing_vectors_without_changing_data(store):
    from alembic import command
    from database.runtime import alembic_config
    from sqlalchemy import text
    from app.models.entities import FaceAngle
    with store.migration.begin() as connection:
        command.downgrade(alembic_config(connection,application_role=store.config.user),'0005_optional_password')
    vectors=[]
    with store.db.transaction() as session:
        _,member,_,_=graph(session)
        for i,angle in enumerate(FaceAngle):
            vector=np.random.default_rng(i).normal(size=512)
            row=EmbeddingRepository(session).create(member.id,vector,angle,'previous-gallery')
            row.is_active=i%2==0
            vectors.append((row.id,np.asarray(row.embedding,dtype=np.float32).tobytes(),row.angle,row.model_version,row.is_active))
    with store.migration.begin() as connection:
        command.upgrade(alembic_config(connection,application_role=store.config.user),'head')
        storage=connection.execute(text("SELECT attstorage FROM pg_attribute WHERE attrelid='face_embeddings'::regclass AND attname='embedding'")).scalar_one()
        options=connection.execute(text("SELECT reloptions FROM pg_class WHERE oid='face_embeddings'::regclass")).scalar_one()
        assert storage=='p' and 'toast_tuple_target=4096' in options
    with store.db.transaction() as session:
        actual=[(row.id,np.asarray(row.embedding,dtype=np.float32).tobytes(),row.angle,row.model_version,row.is_active)
            for row in session.scalars(select(FaceEmbedding).order_by(FaceEmbedding.id))]
        assert actual==vectors


def test_ai_search_active_only_model_version_threshold_and_roundtrip(store):
    one=np.zeros(512);one[0]=1
    other=np.zeros(512);other[1]=1
    version='arcface-synthetic-v1'
    with store.db.transaction() as session:
        group,member,_,_=graph(session)
        active=MemberRepository(session).create('AI-2','Synthetic second',group.id,'synthetic/none.png')
        archived=MemberRepository(session).create('AI-3','Synthetic archived',group.id,'synthetic/none.png')
        repo=EmbeddingRepository(session)
        repo.create(member.id,one*10,'FRONT',version)
        repo.create(active.id,other,'FRONT',version)
        inactive_sample=repo.create(archived.id,one,'FRONT',version)
        inactive_sample.is_active=False
        inactive=MemberRepository(session).create('AI-4','Synthetic inactive',group.id,'synthetic/none.png')
        repo.create(inactive.id,one,'FRONT',version)
        MemberRepository(session).deactivate(inactive.id)
        repo.create(active.id,one,'LEFT','other-model')
        member_id=member.id
    with store.db.transaction() as session:
        decision=identify(session,one,model_version=version)
        assert decision.member_id==member_id and decision.similarity==pytest.approx(1)
        stored=session.scalar(select(FaceEmbedding.embedding).where(FaceEmbedding.member_id==member_id))
        assert np.linalg.norm(stored)==pytest.approx(1)
        assert identify(session,-one,model_version=version).member_id is None
        assert identify(session,one,model_version='missing').similarity is None
        boundary=one*.6+other*.8
        assert identify(session,boundary,model_version=version,threshold=.81).member_id is None
        for threshold in (True,-1,float('nan')):
            with pytest.raises(ValueError):
                identify(session,one,model_version=version,threshold=threshold)


@pytest.mark.models
def test_real_arcface_generated_embedding_pgvector_roundtrip(store):
    from pathlib import Path
    from ai.models import verified_assets
    from ai.recognizer.arcface import ArcFace
    root=Path(__file__).resolve().parents[1]
    assets=verified_assets(root,root/'resources/models')
    recognizer=ArcFace(assets)
    generated=np.random.default_rng(37).integers(0,256,(112,112,3),dtype=np.uint8)
    vector=recognizer.embed(generated)
    with store.db.transaction() as session:
        group,member,_,_=graph(session)
        EmbeddingRepository(session).create(member.id,vector,'FRONT',assets['version'])
        member_id=member.id
    with store.db.transaction() as session:
        result=identify(session,vector.copy(),model_version=assets['version'])
        assert result.member_id==member_id and result.similarity>.999
        assert identify(session,-vector,model_version=assets['version']).member_id is None
        MemberRepository(session).deactivate(member_id)
    with store.db.transaction() as session:
        assert identify(session,vector,model_version=assets['version']).member_id is None
