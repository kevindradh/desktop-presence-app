"""Revision counters reject stale administrative edits without losing changes."""
from alembic import op
import sqlalchemy as sa

revision = "0003_admin"
down_revision = "0002_auth"
branch_labels = depends_on = None


def upgrade():
    for table in ("member_groups", "members", "shifts"):
        op.add_column(table, sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))


def downgrade():
    for table in ("shifts", "members", "member_groups"):
        op.drop_column(table, "revision")
