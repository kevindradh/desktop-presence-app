"""Device source references and optimistic edit revisions; no credentials seeded."""
from alembic import op
import sqlalchemy as sa

revision = "0004_devices"
down_revision = "0003_admin"
branch_labels = depends_on = None


def upgrade():
    op.add_column("devices", sa.Column("camera_index", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("devices", sa.Column("secret_ref", sa.String(64), nullable=True))
    op.add_column("devices", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    op.create_unique_constraint("uq_devices_secret_ref", "devices", ["secret_ref"])


def downgrade():
    op.drop_constraint("uq_devices_secret_ref", "devices", type_="unique")
    for name in ("revision", "secret_ref", "camera_index"):
        op.drop_column("devices", name)
