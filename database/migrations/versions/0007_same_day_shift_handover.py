"""Allow different shifts for one member to share a start date."""
from alembic import op

revision = '0007_same_day_shift'
down_revision = '0006_search_storage'
branch_labels = depends_on = None


def upgrade():
    op.execute('SELECT pg_advisory_xact_lock(734281003)')
    op.create_unique_constraint('uq_shift_assignments_member_shift_start', 'shift_assignments',
                                ['member_id', 'shift_id', 'starts_on'])
    op.drop_constraint('uq_shift_assignments_member_id', 'shift_assignments', type_='unique')


def downgrade():
    op.execute('SELECT pg_advisory_xact_lock(734281003)')
    op.create_unique_constraint('uq_shift_assignments_member_id', 'shift_assignments', ['member_id', 'starts_on'])
    op.drop_constraint('uq_shift_assignments_member_shift_start', 'shift_assignments', type_='unique')
