"""Make password changes voluntary for new and existing accounts."""
from alembic import op
import sqlalchemy as sa

revision = "0005_optional_password"
down_revision = "0004_devices"
branch_labels = depends_on = None


def upgrade():
    op.execute(sa.text("SELECT pg_advisory_xact_lock(734281003)"))
    op.alter_column("users", "must_change_password", existing_type=sa.Boolean(),
                    server_default=sa.false(), existing_nullable=False)
    op.execute(sa.text("UPDATE users SET must_change_password = false WHERE must_change_password"))


def downgrade():
    # Previous per-user flags cannot be reconstructed; never force all existing users.
    op.alter_column("users", "must_change_password", existing_type=sa.Boolean(),
                    server_default=sa.true(), existing_nullable=False)
