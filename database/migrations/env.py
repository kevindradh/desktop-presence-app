from alembic import context

from app.models.entities import Base

config = context.config
connection = config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Use scripts/manage_database.py; migration connection must be provided explicitly.")

context.configure(connection=connection, target_metadata=Base.metadata,
                  version_table_schema=config.attributes.get("schema"),
                  compare_type=True, transaction_per_migration=True,
                  include_object=lambda obj, name, kind, reflected, compare_to:
                      not (kind == "table" and name == "alembic_version"))
with context.begin_transaction():
    context.run_migrations()
