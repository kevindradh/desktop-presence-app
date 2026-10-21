"""Stage 1 checks. No enrollment, attendance or real face data is created."""
import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check_imports():
    packages = {
        "PyQt6": "PyQt6.QtWidgets", "SQLAlchemy": "sqlalchemy",
        "psycopg": "psycopg", "pgvector": "pgvector.sqlalchemy",
        "alembic": "alembic", "bcrypt": "bcrypt", "python-dotenv": "dotenv",
        "numpy": "numpy", "opencv-python": "cv2", "onnx": "onnx",
        "onnxruntime": "onnxruntime", "insightface": "insightface",
        "torch": "torch", "pandas": "pandas", "openpyxl": "openpyxl",
        "reportlab": "reportlab", "pytest": "pytest", "pytest-cov": "pytest_cov",
        "pyinstaller": "PyInstaller",
    }
    assert sys.version_info[:2] == (3, 11), "Expected project Python 3.11"
    versions = {}
    for distribution, module in packages.items():
        importlib.import_module(module)
        versions[distribution] = importlib.metadata.version(distribution)
    from PyQt6.QtCore import QT_VERSION_STR, qVersion
    versions["Qt-compile"] = QT_VERSION_STR
    versions["Qt-runtime"] = qVersion()
    import bcrypt
    password = b"stage-1-ephemeral-smoke"
    hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=4))
    assert hashed != password and bcrypt.checkpw(password, hashed)
    assert not bcrypt.checkpw(b"wrong", hashed)
    return {"python": platform.python_version(), "machine": platform.machine(),
            "packages": versions, "bcrypt": "hash/verify passed (test cost only)"}


def check_database():
    from dotenv import dotenv_values
    import numpy as np
    from pgvector.sqlalchemy import VECTOR
    from sqlalchemy import (Column, Integer, MetaData, Table, create_engine,
                            func, insert, literal, select)
    from sqlalchemy.engine import URL
    from sqlalchemy.exc import ProgrammingError
    env = dotenv_values(ROOT / ".env")
    details = []
    for name in (env["STARGATE_DB_NAME"], env["STARGATE_DB_TEST_NAME"]):
        url = URL.create("postgresql+psycopg", username=env["STARGATE_DB_USER"],
                         password=env["STARGATE_DB_PASSWORD"],
                         host=env["STARGATE_DB_HOST"], port=int(env["STARGATE_DB_PORT"]),
                         database=name)
        engine = create_engine(url, hide_parameters=True,
                               connect_args={"connect_timeout": 5})
        try:
            with engine.begin() as conn:
                version = conn.scalar(select(func.version()))
                ext = Table("pg_extension", MetaData(), Column("extname"),
                            Column("extversion"), schema="pg_catalog")
                extension = conn.scalar(select(ext.c.extversion).where(ext.c.extname == "vector"))
                assert extension, "pgvector not provisioned"
                roles = Table("pg_roles", MetaData(), Column("rolname"),
                              Column("rolsuper"), Column("rolcreatedb"),
                              Column("rolcreaterole"), schema="pg_catalog")
                flags = conn.execute(select(roles.c.rolsuper, roles.c.rolcreatedb,
                                            roles.c.rolcreaterole)
                                     .where(roles.c.rolname == env["STARGATE_DB_USER"])).one()
                assert not any(flags), "App role has administrative privileges"
                assert not conn.scalar(select(func.has_schema_privilege(
                    func.current_user(), "public", "CREATE")))
                table = Table("stargate_stage1_vector_smoke", MetaData(),
                              Column("id", Integer, primary_key=True),
                              Column("embedding", VECTOR(512)), prefixes=["TEMPORARY"],
                              postgresql_on_commit="DROP")
                table.create(conn)
                vector = np.zeros(512, dtype=np.float32)
                vector[0] = 1
                opposite = -vector
                conn.execute(insert(table), [{"id": 1, "embedding": vector},
                                             {"id": 2, "embedding": opposite}])
                nearest = conn.execute(select(table.c.id,
                    table.c.embedding.cosine_distance(vector).label("distance"))
                    .order_by(table.c.embedding.cosine_distance(vector))).all()
                assert nearest[0].id == 1 and abs(nearest[0].distance) < 1e-6
                assert nearest[1].id == 2 and abs(nearest[1].distance - 2) < 1e-6
                stored = conn.scalar(select(table.c.embedding).where(table.c.id == 1))
                assert len(stored) == 512 and np.allclose(stored, vector)
                # Verify that the app role cannot make permanent application tables.
                forbidden = Table("stargate_forbidden_smoke", MetaData(),
                                  Column("id", Integer), schema="public")
                try:
                    with conn.begin_nested():
                        forbidden.create(conn)
                        raise AssertionError("Permanent CREATE unexpectedly allowed")
                except ProgrammingError as error:
                    assert getattr(error.orig, "sqlstate", None) == "42501"
                details.append({"database": name, "server": version.split(" on ")[0],
                                "pgvector": extension, "vector_dimensions": 512,
                                "limited_role": True, "cosine_order": [1, 2]})
            with engine.connect() as conn:
                assert conn.scalar(select(func.to_regclass(literal(
                    "pg_temp.stargate_stage1_vector_smoke")))) is None
        finally:
            engine.dispose()
    return details


def check_models():
    import cv2
    import numpy as np
    import torch
    from insightface.model_zoo import get_model
    from third_party.minifasnet.MiniFASNet import MiniFASNetV2
    manifest = json.loads((ROOT / "models/manifest.json").read_text())
    for asset in manifest["assets"]:
        path = ROOT / asset["path"]
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        assert asset["sha256"] and actual == asset["sha256"], asset["id"]
    model_dir = ROOT / "resources/models"
    detector = cv2.dnn.readNetFromCaffe(str(model_dir / "deploy.prototxt"),
                                      str(model_dir / "Widerface-RetinaFace.caffemodel"))
    detector.setInput(cv2.dnn.blobFromImage(np.zeros((192, 192, 3), dtype=np.uint8),
                                          1.0, mean=(104, 117, 123)), "data")
    detections = detector.forward("detection_out")
    assert detections.size and np.isfinite(detections).all()
    arcface = get_model(str(model_dir / "w600k_r50.onnx"),
                        providers=["CPUExecutionProvider"], download=False)
    assert arcface is not None and arcface.taskname == "recognition"
    embedding = arcface.get_feat(np.zeros((112, 112, 3), dtype=np.uint8))
    assert embedding.shape == (1, 512) and np.isfinite(embedding).all()
    landmarks = get_model(str(model_dir / "2d106det.onnx"),
                          providers=["CPUExecutionProvider"], download=False)
    assert landmarks is not None and landmarks.taskname == "landmark_2d_106"
    torch.set_num_threads(2)
    liveness = MiniFASNetV2(conv6_kernel=(5, 5))
    state = torch.load(model_dir / "2.7_80x80_MiniFASNetV2.pth",
                       map_location="cpu", weights_only=True)
    state = {key.removeprefix("module."): value for key, value in state.items()}
    liveness.load_state_dict(state, strict=True)
    liveness.eval()
    with torch.inference_mode():
        logits = liveness(torch.zeros((1, 3, 80, 80)))
    assert tuple(logits.shape) == (1, 3) and bool(torch.isfinite(logits).all())
    return {"checksums": len(manifest["assets"]), "detector": "RetinaFace Caffe/OpenCV",
            "recognizer": "ArcFace 512D / InsightFace / ONNX CPU",
            "alignment": "106-point auxiliary model loaded; geometry validation in Stage 7",
            "liveness": "MiniFASNetV2 / PyTorch CPU / 3 logits",
            "input": "synthetic zero arrays only; no accuracy/liveness acceptance claim"}


def check_qt(visible=False):
    if not visible:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication, QLabel
    app = QApplication([])
    label = QLabel("StarGate - Tahap 1\nPyQt6 environment smoke test")
    label.setWindowTitle("StarGate - Environment Check")
    label.resize(440, 140)
    label.show()
    ticked = []
    QTimer.singleShot(100, lambda: ticked.append(True))
    QTimer.singleShot(8000 if visible else 300, app.quit)
    code = app.exec()
    assert code == 0 and ticked
    return {"mode": "native" if visible else "offscreen", "event_loop": "PASS",
            "timer": "PASS", "clean_exit": True}


def check_camera(index):
    import cv2
    backend = cv2.CAP_AVFOUNDATION if sys.platform == "darwin" else cv2.CAP_ANY
    camera = cv2.VideoCapture(index, backend)
    try:
        if not camera.isOpened():
            return {"status": "BLOCKED", "reason": "Camera unavailable or permission denied",
                    "index": index, "saved_frames": 0}
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            success, frame = camera.read()
            if success and frame is not None and frame.size:
                return {"status": "PASS", "index": index,
                        "frame_size": [int(frame.shape[1]), int(frame.shape[0])],
                        "saved_frames": 0}
        return {"status": "FAIL", "reason": "Camera opened but no frame received"}
    finally:
        camera.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=["imports", "database", "models", "qt", "camera"])
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks = {"imports": check_imports, "database": check_database, "models": check_models,
              "qt": lambda: check_qt(args.visible),
              "camera": lambda: check_camera(args.camera_index)}
    names = [args.only] if args.only else ["imports", "database", "models", "qt"]
    report = {"stage": 1, "platform": platform.platform(), "checks": {}}
    for name in names:
        try:
            detail = checks[name]()
            status = detail.get("status", "PASS") if isinstance(detail, dict) else "PASS"
            report["checks"][name] = {"status": status, "detail": detail}
        except Exception as error:
            # Do not serialize arbitrary exception strings containing DB credentials.
            report["checks"][name] = {"status": "FAIL", "error_type": type(error).__name__}
            print(f"{name}: {type(error).__name__}", file=sys.stderr)
        print(f"{name}: {report['checks'][name]['status']}", flush=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    else:
        print(json.dumps(report, indent=2))
    return 0 if all(v["status"] == "PASS" for v in report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
