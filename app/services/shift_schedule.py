"""Inclusive assignment dates with a shared day for consecutive shifts."""
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import aliased

from app.models.entities import Shift, ShiftAssignment


def active_on(assignment, day):
    return and_(assignment.starts_on <= day,
                or_(assignment.ends_on.is_(None), assignment.ends_on >= day))


def consecutive(first_assignment, first_shift, second_assignment, second_shift):
    return func.coalesce(and_(first_assignment.ends_on == second_assignment.starts_on,
                              first_shift.start_time < first_shift.end_time,
                              first_shift.end_time <= second_shift.start_time), False)


def conflicting_assignments(member_id, day):
    first, second = aliased(ShiftAssignment), aliased(ShiftAssignment)
    first_shift, second_shift = aliased(Shift), aliased(Shift)
    return (select(first.id).select_from(first)
            .join(second, and_(second.member_id == first.member_id, first.id < second.id))
            .join(first_shift, first_shift.id == first.shift_id)
            .join(second_shift, second_shift.id == second.shift_id)
            .where(first.member_id == member_id, active_on(first, day), active_on(second, day),
                   ~or_(consecutive(first, first_shift, second, second_shift),
                        consecutive(second, second_shift, first, first_shift)))
            .correlate_except(first, second, first_shift, second_shift).exists())
