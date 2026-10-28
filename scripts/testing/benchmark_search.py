"""Exact production search on 10,000 fictional members and 50,000 random vectors."""
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time
import uuid


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=1000)
    args=parser.parse_args()
    assert 1<=args.samples<=1000
    if not getattr(sys,'frozen',False):sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import numpy as np
    from sqlalchemy import DDL,event,func,insert,select,text
    from sqlalchemy.orm import Session
    from sqlalchemy.schema import CreateSchema,DropSchema
    from app.services.database import create_database_engine
    from app.models.entities import Member,MemberGroup,FaceEmbedding,FaceAngle
    from ai.embedding.search import identify
    from database.runtime import connection_config,upgrade
    if getattr(sys,'frozen',False):
        expected=Path(os.environ['LOCALAPPDATA'])/'StarGate-Parallels-0141'
        assert args.data_dir and args.data_dir.resolve()==expected.resolve()
        assert (expected/'.local/managed-postgres/state.json').is_file()
        application=connection_config('dev',root=expected)
        migration=connection_config('dev',migration=True,root=expected)
        assert application.name=='stargate_local'
    else:
        assert args.data_dir is None
        application=connection_config('test')
        migration=connection_config('test',migration=True)
        assert application.name==migration.name=='stargate_test'
    assert application.host in {'localhost','127.0.0.1','::1'}
    assert migration.host==application.host and migration.name==application.name
    schema='stage3_test_'+uuid.uuid4().hex
    admin=create_database_engine(migration)
    writer=reader=None
    created=False
    report={'schema':schema,'members':10000,'embeddings_per_member':5,'embedding_count':50000,
        'dimensions':512,'samples':args.samples,'variant':'production','synthetic_vectors':True,'real_faces':False,
        'platform':platform.platform(),'python_architecture':platform.machine(),
        'method':'production identify / exact cosine / best angle per active member',
        'first_query_is_os_cold':False,'formal_sla_certification':False}
    try:
        with admin.begin() as connection:
            connection.execute(CreateSchema(schema));created=True
            quote=connection.dialect.identifier_preparer.quote
            connection.execute(DDL('GRANT USAGE ON SCHEMA '+quote(schema)+' TO '+quote(application.user)))
        writer=create_database_engine(migration,schema=schema)
        reader=create_database_engine(application,schema=schema)
        with writer.begin() as connection:upgrade(connection,application_role=application.user)
        rng=np.random.default_rng(20261028)
        selected=set(int(value) for value in rng.choice(np.arange(1,10001),size=1000,replace=False))
        probes=[]
        version='synthetic-scale-20261028'
        with Session(writer) as session,session.begin():
            group=MemberGroup(group_name='Benchmark sintetis');session.add(group);session.flush()
            group_id=group.id
        for start in range(1,10001,250):
            count=min(250,10001-start)
            bases=rng.normal(size=(count,512)).astype(np.float32)
            bases/=np.linalg.norm(bases,axis=1,keepdims=True)
            members=[];embeddings=[]
            for offset,base in enumerate(bases):
                identifier=start+offset
                members.append({'id':identifier,'member_code':f'BENCH-{identifier:05}',
                    'full_name':f'Anggota Fiktif {identifier:05}','group_id':group_id,'photo_path':'synthetic/none.png'})
                if identifier in selected:probes.append((identifier,base.copy()))
                for angle in FaceAngle:
                    vector=base+rng.normal(scale=.01,size=512).astype(np.float32)
                    vector/=np.linalg.norm(vector)
                    embeddings.append({'member_id':identifier,'embedding':vector,'angle':angle,'model_version':version})
            with Session(writer) as session,session.begin():
                session.execute(insert(Member),members)
                session.execute(insert(FaceEmbedding),embeddings)
            if start in (1,2501,5001,7501):print('Fixture members: '+str(start+count-1),flush=True)
        with writer.begin() as connection:
            connection.execute(text('ANALYZE '+schema+'.members'))
            connection.execute(text('ANALYZE '+schema+'.face_embeddings'))
            report['storage']=dict(connection.execute(text(
                "SELECT a.attstorage AS policy, pg_relation_size(c.oid) AS heap_bytes, "
                "pg_table_size(c.oid) AS table_bytes FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid "
                "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=:schema "
                "AND c.relname='face_embeddings' AND a.attname='embedding'"),{'schema':schema}).mappings().one())
        durations=[]
        captured={}
        def capture(connection,cursor,statement,parameters,context,many):
            if statement.lstrip().startswith('SELECT') and 'face_embeddings.embedding' in statement:
                captured.update(statement=statement,parameters=parameters)
        event.listen(reader,'before_cursor_execute',capture)
        with Session(reader) as session:
            assert session.scalar(select(func.count()).select_from(Member))==10000
            assert session.scalar(select(func.count()).select_from(FaceEmbedding))==50000
            for index,(identifier,vector) in enumerate(probes[:5]+probes[:args.samples]):
                began=time.perf_counter_ns()
                decision=identify(session,vector,model_version=version)
                elapsed=(time.perf_counter_ns()-began)/1e6
                assert decision.member_id==identifier
                if index==0:report['first_query_ms']=elapsed
                if index>=5:durations.append(elapsed)
                if index in (4,254,504,754,1004):print('Measured queries: '+str(max(0,index-4)),flush=True)
            if captured:
                with session.connection().connection.driver_connection.cursor() as cursor:
                    cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+captured['statement'],captured['parameters'])
                    plan=cursor.fetchone()[0]
                allowed={'Plan','Plans','Node Type','Join Type','Strategy','Actual Startup Time',
                    'Actual Total Time','Actual Rows','Actual Loops','Workers Planned','Workers Launched',
                    'Shared Hit Blocks','Shared Read Blocks','Temp Read Blocks','Temp Written Blocks',
                    'Sort Method','Peak Memory Usage','Planning Time','Execution Time'}
                def safe(value):
                    if isinstance(value,dict):return {key:safe(item) for key,item in value.items() if key in allowed}
                    if isinstance(value,list):return [safe(item) for item in value]
                    return value
                report['query_plan']=safe(plan)
        assert len(durations)==args.samples
        report.update(p50_ms=float(np.percentile(durations,50)),p95_ms=float(np.percentile(durations,95)),
            p99_ms=float(np.percentile(durations,99)),max_ms=max(durations),all_queries_correct=True,
            queries_over_100ms=sum(value>100 for value in durations),latencies_ms=durations)
        report['observed_p95_at_most_100ms']=report['p95_ms']<=100
        report['all_observed_queries_at_most_100ms']=max(durations)<=100
    finally:
        if reader:reader.dispose()
        if writer:writer.dispose()
        if created:
            assert schema.startswith('stage3_test_')
            with admin.begin() as connection:connection.execute(DropSchema(schema,cascade=True))
            report['temporary_schema_removed']=True
        admin.dispose()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key!='latencies_ms'}),flush=True)
    return 0 if report['observed_p95_at_most_100ms'] else 1


if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    try:raise SystemExit(main())
    except Exception as error:
        import traceback
        print(json.dumps({'benchmark':'ERROR','error_type':type(error).__name__,
            'frames':[{'file':Path(frame.filename).name,'function':frame.name,'line':frame.lineno}
                for frame in traceback.extract_tb(error.__traceback__)]}),flush=True)
        raise SystemExit(2)
