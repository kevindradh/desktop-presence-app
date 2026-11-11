"""Keep an attendance session's timezone when the location timezone changes."""
from alembic import op
import sqlalchemy as sa

revision = '0008_attendance_timezone'
down_revision = '0007_same_day_shift'
branch_labels = depends_on = None


def upgrade():
    op.execute('SELECT pg_advisory_xact_lock(734281003)')
    op.add_column('attendance', sa.Column('timezone_name', sa.String(80), nullable=True))
    op.execute(sa.text('UPDATE attendance AS a SET timezone_name = l.timezone '
                       'FROM devices AS d JOIN locations AS l ON l.id = d.location_id '
                       'WHERE a.device_id = d.id'))


def downgrade():
    op.execute('SELECT pg_advisory_xact_lock(734281003)')
    op.drop_column('attendance', 'timezone_name')
