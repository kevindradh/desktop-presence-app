"""Idempotent seed: preserves settings already changed by an administrator."""
from sqlalchemy.dialects.postgresql import insert

from app.models.entities import Location, Setting
from app.repositories.core import AuditRepository
from app.settings.defaults import DEFAULT_SETTINGS


def seed_defaults(session):
    inserted = list(session.scalars(insert(Setting).values([
        {"setting_key": key, "setting_value": value} for key, value in DEFAULT_SETTINGS.items()
    ]).on_conflict_do_nothing(index_elements=[Setting.setting_key]).returning(Setting.id)))
    locations = list(session.scalars(insert(Location).values(location_code="LOCAL",
        location_name="Lokasi utama", timezone="Asia/Jakarta", is_active=True)
        .on_conflict_do_nothing(index_elements=[Location.location_code]).returning(Location.id)))
    if inserted or locations:
        AuditRepository(session).append("system.seeded", "system",
                                         details={"record_count": len(inserted) + len(locations)})
    return {"settings_inserted": len(inserted), "locations_inserted": len(locations)}
