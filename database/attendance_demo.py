"""Stage 10 synthetic fixtures/scenarios. Only use with demo_database's test schema."""
from dataclasses import dataclass, replace
from datetime import datetime, time as daytime, timedelta
from threading import Lock
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import secrets
import time

import numpy as np
from sqlalchemy import select

from ai.attendance_process import signed_packet
from ai.contracts import Analysis
from app.models.entities import Attendance, DeviceType, FaceAngle, Location, Role
from app.repositories.core import (DeviceRepository, EmbeddingRepository, GroupRepository,
    MemberRepository, ShiftRepository, UserRepository)
from app.services.attendance import AttendanceService
from app.services.auth import AuthService, password_hash
from app.services.database import DataValidationError
from app.services.devices import DevicesService
from app.services.settings import SettingsService
from database.demo import demo_database
from database.seed.defaults import seed_defaults

VERSION = 'stage10-demo-synthetic-v1'


class DemoClock:
    def __init__(self):
        self.lock = Lock()
        self.value = datetime.combine(datetime.now(ZoneInfo('Asia/Jakarta')).date(),
                                      daytime(8), ZoneInfo('Asia/Jakarta'))

    def now(self):
        with self.lock:
            return self.value

    def advance(self, seconds):
        with self.lock:
            self.value += timedelta(seconds=seconds)


def analysis(unknown=False):
    vector = np.zeros(512, dtype=np.float32)
    vector[1 if unknown else 0] = 1
    return Analysis('ready', 1, (10, 10, 80, 80), (), .99, 1, vector, 10., VERSION)


def seed_demo(store, config):
    if not store.schema.startswith('stage3_test_') or store.config.name != 'stargate_test':
        raise ValueError('Demo hanya menerima schema database uji miliknya.')
    clock = DemoClock()
    password = secrets.token_urlsafe(24)
    encoded = password_hash(password)
    with store.db.transaction() as session:
        seed_defaults(session)
        user = UserRepository(session).create_with_hash('demo_attendance', 'Penguji Demo', encoded, Role.SUPER_ADMIN)
        user.must_change_password = False
        group = GroupRepository(session).create('Grup Demo Tahap 10')
        member = MemberRepository(session).create('DEMO-10-001', 'Peserta Sintetis', group.id, 'synthetic/no-photo.png')
        shift = ShiftRepository(session).create('Demo 08:00–17:00', daytime(8), daytime(17), 10)
        ShiftRepository(session).assign(member.id, shift.id, clock.now().date(), clock.now().date())
        location = session.scalar(select(Location))
        location.timezone = 'Asia/Jakarta'
        ids = []
        for index in range(2):
            device = DeviceRepository(session).create(f'Kamera sintetis {index+1}', DeviceType.USB, location.id)
            device.camera_index = index
            ids.append(device.id)
        for angle in FaceAngle:
            EmbeddingRepository(session).create(member.id, analysis().embedding, angle, VERSION)
    auth = AuthService(store.db)
    login = auth.login('demo_attendance', password)
    service = AttendanceService(auth, config, DevicesService(auth, config), clock=clock.now)
    return SimpleNamespace(auth=auth, login=login, token=login.token, service=service,
                           clock=clock, devices=ids, sequence={}, store=store)


def events(data):
    with data.store.db.transaction() as session:
        return [dict(event=row.attendance_type.value, time=row.attendance_time.isoformat(),
                     status=row.status.value, automatic=row.is_automatic, early=row.is_early_leave)
                for row in session.scalars(select(Attendance).order_by(Attendance.id))]


def begin(data, mode='AUTO', camera=0):
    return data.service.begin(data.token, [data.devices[camera]], mode)[0].binding


def scan(data, binding=None, value='known'):
    binding = binding or begin(data)
    nonce = binding['nonce']
    sequence = data.sequence.get(nonce, 0) + 1
    data.sequence[nonce] = sequence
    packet = signed_packet(data.service.key, binding, sequence, time.monotonic(),
                           analysis=None if value == 'absence' else analysis(value == 'unknown'))
    return data.service.submit(data.token, packet)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def complete(data):
    binding = begin(data, 'IN')
    require(scan(data, binding).event == 'IN', 'IN harus tersimpan')
    data.clock.advance(61)
    require(not scan(data, binding).saved, 'Wajah terus terlihat tidak boleh tercatat lagi')
    require(not scan(data, begin(data, 'IN')).saved, 'IN kedua harus ditolak')
    for mode in ('BREAK_OUT', 'BREAK_IN', 'OUT'):
        data.clock.advance(61)
        require(scan(data, begin(data, mode)).event == mode, f'{mode} harus tersimpan')
    data.clock.advance(61)
    require(not scan(data).saved, 'Sesi selesai tidak boleh menerima event baru')
    require([row['event'] for row in events(data)] == ['IN', 'BREAK_OUT', 'BREAK_IN', 'OUT'], 'Urutan riwayat salah')


def cooldown(data):
    require(scan(data).saved, 'IN harus tersimpan')
    data.clock.advance(59)
    require(not scan(data, begin(data, camera=1)).saved, 'Duplikat lintas kamera sebelum 60 detik harus ditolak')
    data.clock.advance(2)
    require(scan(data, begin(data, camera=1)).event == 'OUT', 'OUT setelah jeda harus tersimpan')
    require(len(events(data)) == 2, 'Harus hanya ada dua event')


def early(data):
    data.clock.advance(-1)
    require(not scan(data).saved and not events(data), 'Scan sebelum shift harus ditolak')
    data.clock.advance(1)
    require(scan(data).event == 'IN', 'Scan tepat jam mulai harus diizinkan')


def late(data):
    data.clock.advance(601)
    require(scan(data).saved and events(data)[0]['status'] == 'LATE', 'Setelah toleransi harus Late')


def grace(data):
    data.clock.advance(600)
    require(scan(data).saved and events(data)[0]['status'] == 'PRESENT', 'Tepat batas toleransi harus Present')


def unknown(data):
    require(not scan(data, value='unknown').saved and not events(data), 'Wajah tidak dikenal tidak boleh tersimpan')


def spoof(data):
    binding = begin(data)
    packet = signed_packet(data.service.key, binding, 1, time.monotonic(),
                           analysis=replace(analysis(), live_score=.1, live_class=0))
    try:
        data.service.submit(data.token, packet)
    except DataValidationError:
        require(not events(data), 'Probe spoof tidak boleh menulis event')
        return
    raise AssertionError('Probe spoof harus ditolak')


def policy(data):
    binding = begin(data)
    settings = SettingsService(data.auth)
    old = settings.load(data.token)
    settings.save(data.token, dict(old, similarity_threshold=.65), old)
    result = scan(data, binding)
    require(result.restart and not result.saved and not events(data), 'Konfigurasi lama harus ditolak')
    require(scan(data).saved, 'Pemeriksaan baru memakai pengaturan terbaru')


def automatic(data):
    require(scan(data).saved, 'IN harus tersimpan')
    settings = SettingsService(data.auth)
    old = settings.load(data.token)
    settings.save(data.token, dict(old, auto_checkout=True), old)
    data.clock.advance(9*3600)
    require(data.service.auto_checkout(data.token) == 1, 'Harus satu OUT otomatis')
    require(data.service.auto_checkout(data.token) == 0, 'Checkout ulang harus idempoten')
    rows = events(data)
    require(len(rows) == 2 and rows[-1]['event'] == 'OUT' and rows[-1]['automatic'], 'Sumber harus Otomatis')


SCENARIOS = (
    ('Alur lengkap dan wajah terus terlihat', complete),
    ('Jeda lintas dua kamera', cooldown),
    ('Sebelum dan tepat awal shift', early),
    ('Tepat batas toleransi: Present', grace),
    ('Lewat toleransi: Late', late),
    ('Wajah tidak dikenal (sintetis)', unknown),
    ('Probe spoof (sintetis)', spoof),
    ('Perubahan pengaturan saat scan', policy),
    ('Checkout otomatis tanpa duplikat', automatic),
)


def run_scenario(index, config):
    """A fresh owned schema for every scenario, always removed on normal exit."""
    title, operation = SCENARIOS[index]
    try:
        with demo_database() as store:
            data = seed_demo(store, config)
            try:
                operation(data)
                result = dict(name=title, status='LULUS', detail='Hasil sesuai harapan', events=events(data))
            except AssertionError as error:
                result = dict(name=title, status='GAGAL', detail=str(error), events=events(data))
            finally:
                data.service.cancel_all()
        return result
    except Exception:
        # Never serialize connection details, SQL parameters, or signed packets.
        return dict(name=title, status='ERROR', detail='Uji tidak selesai. Periksa PostgreSQL dan konfigurasi database test.', events=[])


def synthetic_camera(spec, pixels, metadata, lock, messages, stop, open_timeout, read_timeout):
    """A colored frame source; never touches a physical camera."""
    try:
        messages.send(('opened', None))
        sequence = 0
        while not stop.is_set():
            with lock:
                memoryview(pixels).cast('B')[:96*96*3] = bytes((20, 100, 60))*(96*96)
                sequence += 1
                metadata[:] = (sequence, 96, 96, time.monotonic(), 96, 96)
            stop.wait(.05)
    finally:
        messages.close()


@dataclass(repr=False)
class SyntheticTarget:
    key: bytes
    binding: dict
    choice: object

    def __call__(self, root, model_dir, options, pixels, shape, lock, connection):
        try:
            sequence = 0
            absent_since = None
            connection.send(dict(event='ready'))
            while connection.recv() != 'stop':
                with lock:
                    np.frombuffer(pixels, dtype=np.uint8).fill(0)
                    shape[:] = (0, 0)
                choice = self.choice.value
                now = time.monotonic()
                response = dict(event='result', status='ready', face_count=1,
                                box=(10, 10, 80, 80), points=(), elapsed_ms=1.)
                packet_value = analysis(choice == 1)
                emit = choice in (0, 1)
                if choice == 2:
                    response.update(status='spoof', live_score=.1, live_class=0)
                elif choice == 3:
                    response.update(status='no_face', face_count=0, box=None)
                    absent_since = now if absent_since is None else absent_since
                    emit = now-absent_since >= 1
                    packet_value = None
                else:
                    response.update(live_score=.99, live_class=1)
                if choice != 3:
                    absent_since = None
                if emit:
                    sequence += 1
                    response['packet'] = signed_packet(self.key, self.binding, sequence, now, analysis=packet_value)
                connection.send(response)
                time.sleep(.05)
        except (EOFError, BrokenPipeError, OSError):
            pass
        finally:
            connection.close()
