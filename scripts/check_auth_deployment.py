"""Read-only Stage 4 deployment proof, no credential/identity payloads."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select
from app.models.entities import AuthSession, User
from app.services.database import create_database_engine
from database.runtime import connection_config, schema_status


def main():
    report = {"stage": 4, "databases": {}}
    for name in ("dev", "test"):
        engine = create_database_engine(connection_config(name))
        try:
            with engine.begin() as connection:
                status = schema_status(connection)
                status["user_count"] = connection.scalar(select(func.count()).select_from(User))
                status["session_count"] = connection.scalar(select(func.count()).select_from(AuthSession))
                report["databases"][name] = status
        finally:
            engine.dispose()
    path = ROOT / "docs/testing/evidence/stage-04-deployment.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    assert all(item["at_head"] and item["schema_valid"] for item in report["databases"].values())
    print("Development/test schema checks: PASS. No account identities or secrets exported.")


if __name__ == "__main__":
    main()
