import numpy as np
import pytest
from sqlalchemy import select
from ai.embedding.search import identify
from app.models.entities import FaceEmbedding
from app.repositories.core import EmbeddingRepository,MemberRepository
from tests.test_database import store,graph

pytestmark=pytest.mark.database


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
