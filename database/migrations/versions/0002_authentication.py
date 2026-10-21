"""Authentication state and hashed revocable tokens."""
from alembic import op
import sqlalchemy as sa

revision = "0002_auth"
down_revision = "0001_stargate"
branch_labels = depends_on = None


def upgrade():
    op.add_column("users", sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))
    op.create_table("auth_sessions",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("is_remember", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default="false", nullable=False))
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    conn = op.get_bind()
    quote = conn.dialect.identifier_preparer.quote
    schema = quote(op.get_context().config.attributes.get("schema") or conn.dialect.default_schema_name)
    role = quote(op.get_context().config.attributes["application_role"])
    op.execute(sa.DDL(f"GRANT SELECT, INSERT, UPDATE ON TABLE {schema}.auth_sessions TO {role}"))
    op.execute(sa.DDL(f"GRANT USAGE, SELECT ON SEQUENCE {schema}.auth_sessions_id_seq TO {role}"))


def downgrade():
    op.drop_table("auth_sessions")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_attempts")
