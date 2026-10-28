"""Keep 512D gallery rows inline for exact search without changing vector values."""
from alembic import op
import sqlalchemy as sa

revision = '0006_search_storage'
down_revision = '0005_optional_password'
branch_labels = depends_on = None


def upgrade():
    op.execute(sa.text('SELECT pg_advisory_xact_lock(734281003)'))
    op.execute(sa.text("SET LOCAL statement_timeout = '120s'"))
    op.execute(sa.text('ALTER TABLE face_embeddings ALTER COLUMN embedding SET STORAGE PLAIN'))
    op.execute(sa.text('ALTER TABLE face_embeddings SET (toast_tuple_target=4096)'))
    # New values force re-storage; changing storage policy alone leaves old TOAST pointers.
    op.execute(sa.text("UPDATE face_embeddings SET embedding=embedding::text::vector(512), "
                       "model_version=model_version || '', angle=angle || ''"))


def downgrade():
    op.execute(sa.text('ALTER TABLE face_embeddings ALTER COLUMN embedding SET STORAGE EXTERNAL'))
    op.execute(sa.text('ALTER TABLE face_embeddings RESET (toast_tuple_target)'))
