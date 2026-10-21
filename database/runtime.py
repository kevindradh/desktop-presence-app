"""Administrative tooling only. Migration secrets do not enter GUI configuration."""
from dataclasses import replace
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from dotenv import dotenv_values
from sqlalchemy import inspect

from app.models.entities import Base
from app.services.database import create_database_engine
from app.settings.config import ConfigError, load_config

from app.settings.paths import runtime_paths
ROOT = runtime_paths().resources


def connection_config(target="dev", *, migration=False, root=None, env_file=None):
    if target not in {"dev", "test"}:
        raise ConfigError("Database target harus dev atau test.")
    root = Path(root) if root is not None else runtime_paths().data
    settings = load_config(root, env_file)
    values = dict(dotenv_values(env_file or root / ".env", interpolate=False))
    values.update({key: val for key, val in os.environ.items() if key.startswith("STARGATE_")})
    config = settings.database
    if target == "test":
        name = values.get("STARGATE_DB_TEST_NAME")
        if not name or name == config.name:
            raise ConfigError("Database uji harus terpisah dari database development.")
        config = replace(config, name=name)
    if migration:
        user = values.get("STARGATE_DB_MIGRATION_USER")
        password = values.get("STARGATE_DB_MIGRATION_PASSWORD")
        if not user or not password or user == settings.database.user:
            raise ConfigError("Akun migrasi terpisah belum dikonfigurasi.")
        config = replace(config, user=user, password=password)
    return config


def alembic_config(connection, *, application_role=None):
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "database/migrations"))
    cfg.attributes["connection"] = connection
    cfg.attributes["application_role"] = application_role or load_config(runtime_paths().data).database.user
    # Each integration run uses its own schema; revision table must follow it.
    cfg.attributes["schema"] = inspect(connection).default_schema_name
    return cfg


def upgrade(connection, *, application_role=None):
    command.upgrade(alembic_config(connection, application_role=application_role), "head")


def schema_status(connection):
    from alembic.script import ScriptDirectory
    cfg = alembic_config(connection)
    expected = ScriptDirectory.from_config(cfg).get_current_head()
    current = MigrationContext.configure(connection, opts={
        "version_table_schema": cfg.attributes["schema"]}).get_current_revision()
    inspector = inspect(connection)
    schema = cfg.attributes["schema"]
    tables = set(inspector.get_table_names(schema=schema))
    missing_tables = sorted(set(Base.metadata.tables) - tables)
    missing_columns = {}
    for name, table in Base.metadata.tables.items():
        if name in tables:
            actual_columns = {column["name"] for column in inspector.get_columns(name, schema=schema)}
            missing = sorted(set(table.columns.keys()) - actual_columns)
            if missing:
                missing_columns[name] = missing
    return {"current_revision": current, "expected_revision": expected,
            "at_head": current == expected and expected is not None,
            "tables": sorted(tables), "application_table_count": len(tables & set(Base.metadata.tables)),
            "schema_valid": not missing_tables and not missing_columns,
            "missing_tables": missing_tables, "missing_columns": missing_columns}
