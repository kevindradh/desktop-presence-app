"""Narrow owner capability for authorized restore, separate from runtime configuration."""
from contextlib import contextmanager
from sqlalchemy import inspect
from app.services.database import create_database_engine, DataValidationError
from database.runtime import connection_config


@contextmanager
def restore_engine(runtime_engine, *, root=None, env_file=None):
    # The desktop helper may only target the configured local development database.
    # Disposable demo/test schemas inject their own owner capability explicitly.
    runtime = connection_config('dev', root=root, env_file=env_file)
    url = runtime_engine.url
    if (url.host, url.port, url.database, url.username) != (runtime.host, runtime.port, runtime.name, runtime.user):
        raise DataValidationError('Target pemulihan tidak sesuai konfigurasi database lokal.')
    with runtime_engine.connect() as conn:
        if inspect(conn).default_schema_name != 'public':
            raise DataValidationError('Target pemulihan tidak sesuai schema aplikasi.')
    engine = create_database_engine(connection_config('dev', migration=True, root=root, env_file=env_file))
    try: yield engine
    finally: engine.dispose()
