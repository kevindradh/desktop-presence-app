import os
from types import SimpleNamespace

import pytest

from app.settings.config import load_config
from scripts import provision_local_db as provision


def test_existing_private_config_is_never_overwritten(tmp_path, monkeypatch):
    env = tmp_path / '.env'
    env.write_text('existing-config')
    monkeypatch.setattr(provision.psycopg, 'connect', lambda **kwargs: pytest.fail('Database must not be contacted'))
    with pytest.raises(SystemExit, match='refusing to overwrite'):
        provision.main(['--data-dir', str(tmp_path), '--admin-host', '/tmp', '--port', '5432'])
    assert env.read_text() == 'existing-config'


@pytest.mark.parametrize('extension_available', [True, False])
def test_private_install_config_uses_bundled_models_and_selected_server(tmp_path, monkeypatch, extension_available):
    connections = []
    mutations = []

    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, query, *args):
            if isinstance(query, str) and query.startswith('SELECT'):
                return SimpleNamespace(fetchone=lambda: (1,) if extension_available and 'pg_available_extensions' in query else None)
            mutations.append(query)

    def connect(**kwargs):
        connections.append(kwargs)
        return Connection()

    monkeypatch.setattr(provision.psycopg, 'connect', connect)
    root = tmp_path / 'Application Support' / 'StarGate'
    command = ['--data-dir', str(root), '--admin-host', '/tmp', '--port', '5432']
    if not extension_available:
        with pytest.raises(SystemExit, match='no roles created'):
            provision.main(command)
        assert not mutations and not root.exists()
        return
    provision.main(command)
    assert {c['host'] for c in connections} == {'/tmp'}
    assert {c['port'] for c in connections} == {5432}
    config = load_config(root, environ={}, bundle_root=tmp_path / 'bundle')
    assert config.database.port == 5432
    assert config.database.user == 'stargate_app'
    assert config.database.password
    assert config.model_dir == tmp_path / 'bundle/resources/models'
    if os.name == 'posix':
        assert (root / '.env').stat().st_mode & 0o777 == 0o600
    assert 'STARGATE_MODEL_DIR' not in (root / '.env').read_text()
