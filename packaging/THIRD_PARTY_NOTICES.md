# StarGate — private research build notices

Purpose declared by the owner on 20 October 2026: competition/research/internal testing. This document does not grant a license to StarGate source, pretrained weights or third-party software, and is not production distribution approval.

- PyQt6: GNU GPL v3 or Riverbank commercial license. A private test executable does not settle obligations when distributing to judges or other organizations. Before external binary distribution, choose a compatible source-distribution arrangement or obtain the required commercial license; preserve Qt/PyQt notices. https://www.riverbankcomputing.com/commercial/license-faq
- Qt: the licenses and exceptions in the installed Qt distribution also apply; retain the bundled license files. https://doc.qt.io/qt-6/licensing.html
- InsightFace code: MIT. The public pretrained ArcFace/landmark models used here are for non-commercial research only unless separately licensed. A competition is not automatically cleared solely by its name. https://github.com/deepinsight/insightface/tree/master/python-package
- MiniFASNet source: Apache-2.0, pinned upstream commit; full license retained in third_party/minifasnet/LICENSE. Model provenance/checksums remain in models/manifest.json. https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
- PyInstaller: GPL with its bootloader exception; this does not replace licenses of bundled libraries. https://pyinstaller.org/en/stable/license.html
- PostgreSQL and pgvector are provisioned separately, not silently installed by the app installer. Preserve their upstream licenses in any separate redistribution. https://www.postgresql.org/about/licence/ and https://github.com/pgvector/pgvector
- NumPy, OpenCV, ONNX/ONNX Runtime, PyTorch, SQLAlchemy, psycopg, Alembic, cryptography, keyring, Pandas, OpenPyXL, ReportLab, bcrypt, python-dotenv and tzdata retain their own copyright/license notices. Installed wheel metadata must be retained; audit the final Windows build's complete dependency inventory before external distribution.

No automatic upload, update or model download occurs during normal application use. Pretrained model inclusion requires the explicit --include-research-models build flag; it is not enabled by default.

Windows dependency versions must be resolved and locked on Windows x64. The macOS arm64 lockfile is evidence for the development host and must not be represented as a tested Windows lock.
