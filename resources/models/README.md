# Model assets

Model binaries are local assets and are excluded from Git. See the tracked
`models/manifest.json` for upstream sources, versions, hashes and usage limits.
Run `scripts/download_models.py` explicitly to download and verify assets.
Loading weights is an environment smoke test, not proof of recognition accuracy,
liveness quality or the attendance SLA. No face samples are collected by downloads.

