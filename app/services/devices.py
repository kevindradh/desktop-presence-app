"""Authorized device CRUD; only redacted RTSP endpoints leave this boundary."""
from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from sqlalchemy import func, select

from app.models.entities import Attendance, Device, DeviceType, Location
from app.repositories.core import AuditRepository
from app.services.administration import clean, identifier
from app.services.camera_capture import CaptureSpec
from app.services.database import DataValidationError
from app.services.device_secrets import DeviceSecretStore

RESOLUTIONS = ("640x480", "1280x720", "1920x1080")


def validate_rtsp(source):
    try:
        if not isinstance(source, str) or not 1 <= len(source) <= 4096 or any(ord(c) <= 32 for c in source):
            raise ValueError
        parsed = urlsplit(source)
        if parsed.scheme.lower() != "rtsp" or not parsed.hostname or parsed.fragment or "\\" in source:
            raise ValueError
        port = parsed.port
        if port is not None and not 1 <= port <= 65535:
            raise ValueError
        host = parsed.hostname
        if any(c in host for c in ("@", "/", "%")):
            raise ValueError
        host = f"[{host}]" if ":" in host else host
        return f"rtsp://{host}" + (f":{port}" if port else "") + "/"
    except (ValueError, TypeError):
        raise DataValidationError("Sumber RTSP harus URL rtsp:// dengan alamat host dan port yang valid.") from None


@dataclass(frozen=True)
class LocationData:
    id: int
    name: str


@dataclass(frozen=True)
class DeviceData:
    id: int
    name: str
    kind: DeviceType
    camera_index: int | None
    rtsp_display: str
    has_source: bool
    resolution: str
    fps: int
    location_id: int
    location_name: str
    revision: int


@dataclass(frozen=True)
class DevicesData:
    devices: tuple[DeviceData, ...]
    locations: tuple[LocationData, ...]


class DevicesService:
    def __init__(self, auth, config, *, secrets=None):
        self.auth = auth
        self.config = config
        self.secrets = secrets or DeviceSecretStore(config)

    def _run(self, token, action):
        return self.auth._protected(token, "devices", action)

    @staticmethod
    def _row(session, device_id, revision=None):
        row = session.scalar(select(Device).where(Device.id == identifier(device_id)).with_for_update())
        if row is None:
            raise DataValidationError("Perangkat tidak ditemukan. Muat ulang daftar.")
        if revision is not None and (type(revision) is not int or row.revision != revision):
            raise DataValidationError("Perangkat telah berubah. Muat ulang sebelum menyimpan.")
        return row

    @staticmethod
    def _data(session, row):
        # Old unredacted values must never be reflected back into a widget or DTO.
        display = validate_rtsp(row.rtsp_url) if row.rtsp_url else ""
        return DeviceData(row.id, row.device_name, row.device_type, row.camera_index,
            display, bool(row.secret_ref), row.resolution, row.fps, row.location_id,
            session.get(Location, row.location_id).location_name, row.revision)

    def list(self, token):
        def operation(session, actor):
            devices = tuple(self._data(session, row) for row in session.scalars(
                select(Device).order_by(func.lower(Device.device_name), Device.id)))
            locations = tuple(LocationData(row.id, row.location_name) for row in session.scalars(
                select(Location).where(Location.is_active.is_(True)).order_by(Location.location_name)))
            return DevicesData(devices, locations)
        return self._run(token, operation)

    def save(self, token, name, kind, resolution, fps, location_id, *, camera_index=0,
             rtsp_source=None, device_id=None, revision=None):
        created, obsolete = [], []
        def operation(session, actor):
            title = clean(name, 160, mandatory=True)
            try:
                entry = DeviceType(kind)
            except (ValueError, TypeError):
                raise DataValidationError("Jenis kamera tidak valid.") from None
            if resolution not in RESOLUTIONS or type(fps) is not int or not 1 <= fps <= 60:
                raise DataValidationError("Pilih resolusi yang tersedia dan FPS antara 1–60.")
            location = session.get(Location, identifier(location_id))
            if location is None or not location.is_active:
                raise DataValidationError("Pilih lokasi aktif yang valid.")
            if entry != DeviceType.RTSP and (type(camera_index) is not int or not 0 <= camera_index <= 15):
                raise DataValidationError("Nomor kamera lokal harus antara 0–15.")
            existing = None if device_id is None else self._row(session, device_id, identifier(revision))
            duplicate = session.scalar(select(Device.id).where(func.lower(Device.device_name) == title.lower(),
                Device.id != device_id if device_id is not None else True).limit(1))
            if duplicate is not None:
                raise DataValidationError("Nama perangkat sudah digunakan.")
            row = existing or Device()
            old_reference = row.secret_ref
            endpoint, reference = None, None
            if entry == DeviceType.RTSP:
                if rtsp_source is not None:
                    endpoint = validate_rtsp(rtsp_source)
                    reference = self.secrets.write(rtsp_source)
                    created.append(reference)
                elif existing and existing.device_type == DeviceType.RTSP and existing.secret_ref:
                    endpoint, reference = existing.rtsp_url, existing.secret_ref
                else:
                    raise DataValidationError("Isi sumber RTSP untuk perangkat ini.")
            elif rtsp_source:
                raise DataValidationError("Kamera lokal tidak menggunakan sumber RTSP.")
            values = dict(device_name=title, device_type=entry, resolution=resolution, fps=fps,
                location_id=location.id, camera_index=None if entry == DeviceType.RTSP else camera_index,
                rtsp_url=endpoint, secret_ref=reference)
            changed = [key for key, value in values.items() if getattr(row, key, None) != value]
            for key, value in values.items():
                setattr(row, key, value)
            if existing is None:
                session.add(row)
            elif changed:
                row.revision += 1
            session.flush()
            if existing is None or changed:
                AuditRepository(session).append("device.created" if existing is None else "device.updated",
                    "device", row.id, actor_id=actor.id, details={"changed_fields": changed})
            if old_reference and old_reference != reference:
                obsolete.append(old_reference)
            return self._data(session, row)
        try:
            result = self._run(token, operation)
        except Exception:
            for reference in created:
                self.secrets.discard(reference)
            raise
        for reference in obsolete:
            self.secrets.discard(reference)
        return result

    def delete(self, token, device_id, revision):
        obsolete = []
        def operation(session, actor):
            row = self._row(session, device_id, identifier(revision))
            if session.scalar(select(Attendance.id).where(Attendance.device_id == row.id).limit(1)) is not None:
                raise DataValidationError("Perangkat memiliki riwayat kehadiran dan tidak dapat dihapus.")
            if row.secret_ref:
                obsolete.append(row.secret_ref)
            AuditRepository(session).append("device.deleted", "device", row.id, actor_id=actor.id)
            session.delete(row)
        self._run(token, operation)
        for reference in obsolete:
            self.secrets.discard(reference)

    def sources(self, token, device_ids):
        def operation(session, actor):
            return self._sources(session, device_ids)
        return self._run(token, operation)

    def _sources(self, session, device_ids):
        # Called only inside a protected devices/attendance transaction.
        if not isinstance(device_ids, (list, tuple)) or not device_ids or len(device_ids) > self.config.camera_max_streams:
            raise DataValidationError("Jumlah kamera terpilih melebihi batas pratinjau.")
        identifiers = tuple(identifier(value) for value in device_ids)
        if len(set(identifiers)) != len(identifiers):
            raise DataValidationError("Perangkat yang sama dipilih lebih dari sekali.")
        result = []
        for device_id in identifiers:
            row = self._row(session, device_id)
            if row.resolution not in RESOLUTIONS or not 1 <= row.fps <= 60:
                raise DataValidationError("Konfigurasi perangkat lama perlu diperbarui sebelum pratinjau.")
            source = self.secrets.read(row.secret_ref) if row.device_type == DeviceType.RTSP else ""
            if source:
                validate_rtsp(source)
            width, height = map(int, row.resolution.split("x"))
            result.append(CaptureSpec(row.id, row.device_name, row.device_type.value,
                row.camera_index or 0, width, height, row.fps, source))
        return tuple(result)
