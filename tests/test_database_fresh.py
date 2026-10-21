"""Fresh reset is destructive only inside explicitly owned disposable test schemas."""
from types import SimpleNamespace

import pytest
from sqlalchemy import select,func,text

from app.models.entities import Base,Member
from app.services.auth import AuthService
from app.services.database import DataValidationError
from app.settings.config import DatabaseConfig
from database.runtime import fresh,schema_status
from scripts.manage_database import confirm_fresh,main
from tests.test_database import store,graph


@pytest.mark.parametrize('host,name,confirmation',[
    ('127.0.0.1','stargate_dev','wrong'),
    ('127.0.0.1','stargate_dev',None),
    ('example.invalid','stargate_dev','stargate_dev'),
    ('127.0.0.1','postgres','postgres'),
    ('127.0.0.1','template1','template1'),
])
def test_fresh_rejects_missing_or_wrong_confirmation_remote_and_system_databases(monkeypatch,host,name,confirmation):
    monkeypatch.setattr('sys.stdin',SimpleNamespace(isatty=lambda:False))
    with pytest.raises(DataValidationError):
        confirm_fresh(DatabaseConfig(host=host,name=name),confirmation)


def test_fresh_accepts_matching_flag_or_interactive_name(monkeypatch,capsys):
    config=DatabaseConfig(name='stargate_dev',password='synthetic-private-password')
    confirm_fresh(config,'stargate_dev')
    monkeypatch.setattr('sys.stdin',SimpleNamespace(isatty=lambda:True))
    monkeypatch.setattr('builtins.input',lambda prompt:'stargate_dev')
    confirm_fresh(config,None)
    assert config.password not in capsys.readouterr().out


def test_fresh_cli_refuses_before_opening_any_database(monkeypatch,capsys):
    import database.runtime as runtime
    import app.services.database as db
    opened=[]
    monkeypatch.setattr(runtime,'connection_config',lambda *a,**kw:DatabaseConfig(name='stargate_dev'))
    monkeypatch.setattr(db,'create_database_engine',lambda *a,**kw:opened.append(True))
    assert main(['fresh','--confirm-database','different'])==2
    assert not opened and 'Nama konfirmasi tidak cocok' in capsys.readouterr().err


@pytest.mark.database
def test_fresh_recreates_tables_defaults_without_accounts_and_is_repeatable(store):
    with store.db.transaction() as session:
        graph(session)
    AuthService(store.db).bootstrap('before-reset','Penguji','Synthetic-fresh-2026!')
    for _ in range(2):
        with store.migration.begin() as connection:
            result=fresh(connection,application_role=store.config.user)
            assert result['schema']['at_head'] and result['schema']['schema_valid']
            assert result['seed']=={'settings_inserted':12,'locations_inserted':1}
            assert connection.scalar(text("SELECT to_regtype('vector') IS NOT NULL"))
        with store.db.transaction() as session:
            counts={name:session.scalar(select(func.count()).select_from(table))
                    for name,table in Base.metadata.tables.items()}
        assert all(count==0 for name,count in counts.items() if name not in {'settings','locations','audit_logs'})
        assert counts['settings']==12 and counts['locations']==counts['audit_logs']==1
        assert AuthService(store.db).bootstrap_required()


@pytest.mark.database
def test_failed_fresh_rolls_back_original_data_and_schema(store,monkeypatch):
    import database.seed.defaults as seed
    with store.db.transaction() as session:
        _,member,_,_=graph(session)
        member_id=member.id
    def fail(*args):raise RuntimeError('Synthetic seed failure')
    monkeypatch.setattr(seed,'seed_defaults',fail)
    with pytest.raises(RuntimeError):
        with store.migration.begin() as connection:
            fresh(connection,application_role=store.config.user)
    with store.db.transaction() as session:
        assert session.get(Member,member_id) is not None
    with store.migration.connect() as connection:
        assert schema_status(connection)['at_head'] and schema_status(connection)['schema_valid']


@pytest.mark.database
def test_fresh_rejects_unrelated_tables_without_removing_any_data(store):
    with store.db.transaction() as session:
        _,member,_,_=graph(session)
        member_id=member.id
    with store.migration.begin() as connection:
        connection.execute(text('CREATE TABLE unrelated (id integer PRIMARY KEY)'))
        connection.execute(text('INSERT INTO unrelated VALUES (17)'))
    with pytest.raises(DataValidationError,match='di luar StarGate'):
        with store.migration.begin() as connection:
            fresh(connection,application_role=store.config.user)
    with store.migration.connect() as connection:
        assert connection.scalar(text('SELECT id FROM unrelated'))==17
    with store.db.transaction() as session:
        assert session.get(Member,member_id) is not None


@pytest.mark.database
def test_fresh_initializes_an_empty_schema(store):
    from alembic import command
    from database.runtime import alembic_config
    with store.migration.begin() as connection:
        command.downgrade(alembic_config(connection,application_role=store.config.user),'base')
        connection.execute(text('DROP TABLE alembic_version'))
        result=fresh(connection,application_role=store.config.user)
        assert result['schema']['at_head'] and result['schema']['schema_valid']
