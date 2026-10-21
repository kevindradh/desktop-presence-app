"""Explicit restart test using only a disposable schema in the test database."""
import argparse
from datetime import date, datetime, time, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restart-local", action="store_true",
                        help="Required: acknowledge brief restart of project-local PostgreSQL")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/testing/evidence/stage-03-persistence.json")
    args = parser.parse_args()
    if not args.restart_local:
        parser.error("Use --restart-local to explicitly run the local development cluster restart")
    from sqlalchemy import DDL, func, select
    from sqlalchemy.schema import CreateSchema, DropSchema
    from app.models.entities import (AttendanceStatus, AttendanceType, Base, DeviceType,
                                    FaceAngle, FaceEmbedding, Location, Member, Setting)
    from app.repositories.core import (AttendanceRepository, DeviceRepository, EmbeddingRepository,
                                       GroupRepository, MemberRepository, ShiftRepository)
    from app.services.bootstrap_admin import bootstrap_super_admin
    from app.services.database import Database, create_database_engine
    from database.runtime import connection_config, upgrade
    from database.seed.defaults import seed_defaults

    config = connection_config("test")
    if config.host != "127.0.0.1" or config.port != 55432:
        raise SystemExit("Restart smoke only supports the project-local 127.0.0.1:55432 cluster")
    schema = "stage3_test_" + uuid.uuid4().hex
    admin = create_database_engine(connection_config("test", migration=True))
    application = migrator = None
    created = stopped = False
    report = {"stage": 3, "schema": schema, "checks": {},
              "scope": "Synthetic data only; no changes to public application data"}

    def local(action):
        return subprocess.run([sys.executable, str(ROOT / "scripts/local_postgres.py"), action],
                              capture_output=True, text=True, timeout=30)

    def snapshot(engine):
        with Database(engine).transaction() as session:
            counts = {name: session.scalar(select(func.count()).select_from(table))
                      for name, table in Base.metadata.tables.items()}
            member = session.scalar(select(Member))
            vector = session.scalar(select(FaceEmbedding.embedding))
            settings = dict(session.execute(select(Setting.setting_key, Setting.setting_value)).all())
            event = AttendanceRepository(session).history(member.id)[0]
            # Hash only the controlled synthetic snapshot; no raw vector written to report.
            payload = {"counts": counts, "member": member.member_code,
                       "settings": settings, "vector": [float(v) for v in vector],
                       "event": [event.attendance_type.value, event.work_date.isoformat(),
                                 event.attendance_time.isoformat()]}
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            started = session.scalar(select(func.pg_postmaster_start_time())).isoformat()
            return {"counts": counts, "snapshot_sha256": digest, "server_started": started}

    try:
        with admin.begin() as conn:
            conn.execute(CreateSchema(schema))
            created = True
            quote = conn.dialect.identifier_preparer.quote
            conn.execute(DDL(f"GRANT USAGE ON SCHEMA {quote(schema)} TO {quote(config.user)}"))
        migrator = create_database_engine(connection_config("test", migration=True), schema=schema)
        with migrator.begin() as conn:
            upgrade(conn)
        migrator.dispose()
        application = create_database_engine(config, schema=schema)
        with Database(application).transaction() as session:
            seed_defaults(session)
            location = session.scalar(select(Location))
            admin_user = bootstrap_super_admin(session, "persistence_admin", "Admin Uji",
                                                "synthetic-persistence-password")
            group = GroupRepository(session).create("Persistence Test", actor_id=admin_user.id)
            member = MemberRepository(session).create("SG-PERSIST-TEST", "Anggota Sintetis", group.id,
                                                       "synthetic/no-photo.jpg", actor_id=admin_user.id)
            shift = ShiftRepository(session).create("Pagi Uji", time(8), time(17), 10)
            ShiftRepository(session).assign(member.id, shift.id, date(2026, 10, 18))
            device = DeviceRepository(session).create("Camera Stub", DeviceType.USB, location.id)
            EmbeddingRepository(session).create(member.id, [1.0]+[0.0]*511, FaceAngle.FRONT, "synthetic")
            AttendanceRepository(session).record(member_id=member.id, device_id=device.id,
                shift_id=shift.id, event_type=AttendanceType.IN, status=AttendanceStatus.PRESENT,
                work_date=date(2026, 10, 18), timestamp=datetime(2026,10,18,1,5,tzinfo=timezone.utc))
        before = snapshot(application)
        application.dispose()
        admin.dispose()
        result = local("stop")
        if result.returncode:
            raise RuntimeError("Project cluster did not stop")
        stopped = True
        result = local("start")
        if result.returncode:
            raise RuntimeError("Project cluster did not start")
        stopped = False
        after = snapshot(application)
        assert before["snapshot_sha256"] == after["snapshot_sha256"]
        assert before["counts"] == after["counts"]
        assert before["server_started"] != after["server_started"]
        report["checks"]["restart_persistence"] = {"status": "PASS", "before": before, "after": after}
    except Exception as error:
        report["checks"]["restart_persistence"] = {"status": "FAIL", "error_type": type(error).__name__}
    finally:
        if stopped:
            local("start")
        if application:
            application.dispose()
        if migrator:
            migrator.dispose()
        if created:
            try:
                with admin.begin() as conn:
                    assert schema.startswith("stage3_test_")
                    conn.execute(DropSchema(schema, cascade=True))
                report["checks"]["temporary_schema_cleanup"] = {"status": "PASS"}
            except Exception as error:
                report["checks"]["temporary_schema_cleanup"] = {
                    "status": "FAIL", "error_type": type(error).__name__}
        admin.dispose()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+"\n")
    for key, value in report["checks"].items():
        print(f"{key}: {value['status']}")
    return 0 if report["checks"] and all(x["status"] == "PASS"
                                        for x in report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
