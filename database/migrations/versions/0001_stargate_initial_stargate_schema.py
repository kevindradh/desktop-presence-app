"""Initial StarGate schema

Revision ID: 0001_stargate
Revises: 
"""
from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy
from sqlalchemy.dialects import postgresql

revision = '0001_stargate'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Static revision: do not import live ORM metadata here.
    op.create_table('locations',
    sa.Column('location_code', sa.String(length=40), nullable=False),
    sa.Column('location_name', sa.String(length=160), nullable=False),
    sa.Column('timezone', sa.String(length=80), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(trim(location_code)) > 0', name=op.f('ck_locations_code_not_empty')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_locations')),
    sa.UniqueConstraint('location_code', name=op.f('uq_locations_location_code'))
    )
    op.create_table('member_groups',
    sa.Column('group_name', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(trim(group_name)) > 0', name=op.f('ck_member_groups_name_not_empty')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_member_groups'))
    )
    op.create_index('uq_member_groups_name_ci', 'member_groups', [sa.literal_column('lower(group_name)')], unique=True)
    op.create_table('settings',
    sa.Column('setting_key', sa.String(length=80), nullable=False),
    sa.Column('setting_value', postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_settings')),
    sa.UniqueConstraint('setting_key', name=op.f('uq_settings_setting_key'))
    )
    op.create_table('shifts',
    sa.Column('shift_name', sa.String(length=120), nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.Column('grace_minutes', sa.Integer(), server_default='0', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('grace_minutes >= 0 AND grace_minutes < 1440', name=op.f('ck_shifts_grace_range')),
    sa.CheckConstraint('length(trim(shift_name)) > 0', name=op.f('ck_shifts_name_not_empty')),
    sa.CheckConstraint('start_time <> end_time', name=op.f('ck_shifts_nonzero_duration')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_shifts')),
    sa.UniqueConstraint('shift_name', name=op.f('uq_shifts_shift_name'))
    )
    op.create_table('users',
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('fullname', sa.String(length=200), nullable=False),
    sa.Column('role', sa.Enum('SUPER_ADMIN', 'ADMIN', 'OPERATOR', 'VIEWER', name='user_role', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('must_change_password', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(trim(fullname)) > 0', name=op.f('ck_users_name_not_empty')),
    sa.CheckConstraint('length(trim(username)) > 0', name=op.f('ck_users_username_not_empty')),
    sa.CheckConstraint("length(password_hash) = 60 AND substring(password_hash from 1 for 4) IN ('$2a$', '$2b$', '$2y$')", name=op.f('ck_users_bcrypt_hash_format')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index('uq_users_username_ci', 'users', [sa.literal_column('lower(username)')], unique=True)
    op.create_table('audit_logs',
    sa.Column('actor_id', sa.BigInteger(), nullable=True),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=False),
    sa.Column('entity_id', sa.BigInteger(), nullable=True),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(trim(action)) > 0', name=op.f('ck_audit_logs_action_not_empty')),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_audit_logs_actor_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_table('calendar_days',
    sa.Column('location_id', sa.BigInteger(), nullable=False),
    sa.Column('calendar_date', sa.Date(), nullable=False),
    sa.Column('is_workday', sa.Boolean(), nullable=False),
    sa.Column('label', sa.String(length=160), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], name=op.f('fk_calendar_days_location_id_locations'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_calendar_days')),
    sa.UniqueConstraint('location_id', 'calendar_date', name=op.f('uq_calendar_days_location_id'))
    )
    op.create_table('devices',
    sa.Column('device_name', sa.String(length=160), nullable=False),
    sa.Column('device_type', sa.Enum('INTERNAL', 'USB', 'RTSP', name='device_type', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('rtsp_url', sa.Text(), nullable=True),
    sa.Column('resolution', sa.String(length=32), nullable=False),
    sa.Column('fps', sa.Integer(), server_default='30', nullable=False),
    sa.Column('location_id', sa.BigInteger(), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('fps > 0 AND fps <= 240', name=op.f('ck_devices_fps_range')),
    sa.CheckConstraint('length(trim(device_name)) > 0', name=op.f('ck_devices_name_not_empty')),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], name=op.f('fk_devices_location_id_locations'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_devices')),
    sa.UniqueConstraint('device_name', name=op.f('uq_devices_device_name'))
    )
    op.create_index(op.f('ix_devices_location_id'), 'devices', ['location_id'], unique=False)
    op.create_table('members',
    sa.Column('member_code', sa.String(length=64), nullable=False),
    sa.Column('full_name', sa.String(length=200), nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=True),
    sa.Column('phone', sa.String(length=40), nullable=True),
    sa.Column('position', sa.String(length=160), nullable=True),
    sa.Column('photo_path', sa.Text(), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(trim(full_name)) > 0', name=op.f('ck_members_name_not_empty')),
    sa.CheckConstraint('length(trim(member_code)) > 0', name=op.f('ck_members_code_not_empty')),
    sa.CheckConstraint('length(trim(photo_path)) > 0', name=op.f('ck_members_photo_not_empty')),
    sa.ForeignKeyConstraint(['group_id'], ['member_groups.id'], name=op.f('fk_members_group_id_member_groups'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_members'))
    )
    op.create_index(op.f('ix_members_group_id'), 'members', ['group_id'], unique=False)
    op.create_index(op.f('ix_members_is_active'), 'members', ['is_active'], unique=False)
    op.create_index('uq_members_code_ci', 'members', [sa.literal_column('lower(member_code)')], unique=True)
    op.create_table('attendance',
    sa.Column('member_id', sa.BigInteger(), nullable=False),
    sa.Column('device_id', sa.BigInteger(), nullable=False),
    sa.Column('shift_id', sa.BigInteger(), nullable=False),
    sa.Column('attendance_type', sa.Enum('IN', 'OUT', 'BREAK_OUT', 'BREAK_IN', name='attendance_type', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('attendance_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.Enum('PRESENT', 'LATE', name='attendance_status', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('work_date', sa.Date(), nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=False),
    sa.Column('is_early_leave', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('is_automatic', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], name=op.f('fk_attendance_device_id_devices'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['group_id'], ['member_groups.id'], name=op.f('fk_attendance_group_id_member_groups'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], name=op.f('fk_attendance_member_id_members'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['shift_id'], ['shifts.id'], name=op.f('fk_attendance_shift_id_shifts'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_attendance'))
    )
    op.create_index(op.f('ix_attendance_attendance_time'), 'attendance', ['attendance_time'], unique=False)
    op.create_index(op.f('ix_attendance_member_id'), 'attendance', ['member_id'], unique=False)
    op.create_index(op.f('ix_attendance_shift_id'), 'attendance', ['shift_id'], unique=False)
    op.create_index(op.f('ix_attendance_work_date'), 'attendance', ['work_date'], unique=False)
    op.create_index('uq_attendance_single_in_out', 'attendance', ['member_id', 'shift_id', 'work_date', 'attendance_type'], unique=True, postgresql_where=sa.text("attendance_type IN ('IN', 'OUT')"))
    op.create_table('face_embeddings',
    sa.Column('member_id', sa.BigInteger(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=512), nullable=False),
    sa.Column('angle', sa.Enum('FRONT', 'LEFT', 'RIGHT', 'UP', 'DOWN', name='face_angle', native_enum=False, create_constraint=True), nullable=False),
    sa.Column('model_version', sa.String(length=120), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(trim(model_version)) > 0', name=op.f('ck_face_embeddings_model_not_empty')),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], name=op.f('fk_face_embeddings_member_id_members'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_face_embeddings'))
    )
    op.create_index(op.f('ix_face_embeddings_member_id'), 'face_embeddings', ['member_id'], unique=False)
    op.create_table('member_leaves',
    sa.Column('member_id', sa.BigInteger(), nullable=False),
    sa.Column('starts_on', sa.Date(), nullable=False),
    sa.Column('ends_on', sa.Date(), nullable=False),
    sa.Column('leave_type', sa.String(length=40), nullable=False),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('ends_on >= starts_on', name=op.f('ck_member_leaves_date_range')),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], name=op.f('fk_member_leaves_member_id_members'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_member_leaves'))
    )
    op.create_index(op.f('ix_member_leaves_member_id'), 'member_leaves', ['member_id'], unique=False)
    op.create_table('shift_assignments',
    sa.Column('member_id', sa.BigInteger(), nullable=False),
    sa.Column('shift_id', sa.BigInteger(), nullable=False),
    sa.Column('starts_on', sa.Date(), nullable=False),
    sa.Column('ends_on', sa.Date(), nullable=True),
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('ends_on IS NULL OR ends_on >= starts_on', name=op.f('ck_shift_assignments_date_range')),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], name=op.f('fk_shift_assignments_member_id_members'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['shift_id'], ['shifts.id'], name=op.f('fk_shift_assignments_shift_id_shifts'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_shift_assignments')),
    sa.UniqueConstraint('member_id', 'starts_on', name=op.f('uq_shift_assignments_member_id'))
    )
    op.create_index(op.f('ix_shift_assignments_member_id'), 'shift_assignments', ['member_id'], unique=False)
    op.create_index(op.f('ix_shift_assignments_shift_id'), 'shift_assignments', ['shift_id'], unique=False)


    _application_permissions()


def downgrade():
    # Static revision: do not import live ORM metadata here.
    op.drop_index(op.f('ix_shift_assignments_shift_id'), table_name='shift_assignments')
    op.drop_index(op.f('ix_shift_assignments_member_id'), table_name='shift_assignments')
    op.drop_table('shift_assignments')
    op.drop_index(op.f('ix_member_leaves_member_id'), table_name='member_leaves')
    op.drop_table('member_leaves')
    op.drop_index(op.f('ix_face_embeddings_member_id'), table_name='face_embeddings')
    op.drop_table('face_embeddings')
    op.drop_index('uq_attendance_single_in_out', table_name='attendance', postgresql_where=sa.text("attendance_type IN ('IN', 'OUT')"))
    op.drop_index(op.f('ix_attendance_work_date'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_shift_id'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_member_id'), table_name='attendance')
    op.drop_index(op.f('ix_attendance_attendance_time'), table_name='attendance')
    op.drop_table('attendance')
    op.drop_index('uq_members_code_ci', table_name='members')
    op.drop_index(op.f('ix_members_is_active'), table_name='members')
    op.drop_index(op.f('ix_members_group_id'), table_name='members')
    op.drop_table('members')
    op.drop_index(op.f('ix_devices_location_id'), table_name='devices')
    op.drop_table('devices')
    op.drop_table('calendar_days')
    op.drop_index(op.f('ix_audit_logs_actor_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('uq_users_username_ci', table_name='users')
    op.drop_table('users')
    op.drop_table('shifts')
    op.drop_table('settings')
    op.drop_index('uq_member_groups_name_ci', table_name='member_groups')
    op.drop_table('member_groups')
    op.drop_table('locations')



def _application_permissions():
    # DDL only; role/schema identifiers are quoted, never string SQL data values.
    context = op.get_context()
    connection = op.get_bind()
    quote = connection.dialect.identifier_preparer.quote
    schema = context.config.attributes.get("schema") or connection.dialect.default_schema_name
    role = quote(context.config.attributes["application_role"])
    tables = ("locations", "member_groups", "settings", "shifts", "users", "audit_logs",
              "calendar_days", "devices", "members", "attendance", "face_embeddings",
              "member_leaves", "shift_assignments")
    for table in tables:
        qualified = f"{quote(schema)}.{quote(table)}"
        op.execute(sa.DDL(f"REVOKE ALL ON TABLE {qualified} FROM {role}"))
        permissions = "SELECT, INSERT" if table == "audit_logs" else "SELECT, INSERT, UPDATE"
        if table not in {"audit_logs", "members", "users"}:
            permissions += ", DELETE"
        op.execute(sa.DDL(f"GRANT {permissions} ON TABLE {qualified} TO {role}"))
        sequence = f"{quote(schema)}.{quote(table + '_id_seq')}"
        op.execute(sa.DDL(f"GRANT USAGE, SELECT ON SEQUENCE {sequence} TO {role}"))
    version = f"{quote(schema)}.alembic_version"
    op.execute(sa.DDL(f"REVOKE ALL ON TABLE {version} FROM {role}"))
    op.execute(sa.DDL(f"GRANT SELECT ON TABLE {version} TO {role}"))
