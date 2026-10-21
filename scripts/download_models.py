"""Explicit asset download; verified local cache, no automatic runtime download."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "models/manifest.json"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "StarGate-dev-setup"})
    with urllib.request.urlopen(request, timeout=90) as source, path.open("wb") as out:
        shutil.copyfileobj(source, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-initial-hashes", action="store_true")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    for asset in manifest["assets"]:
        expected = asset["sha256"]
        if not expected and not args.record_initial_hashes:
            raise SystemExit(f"Unenrolled checksum: {asset['id']}")
        target = ROOT / asset["path"]
        if target.exists():
            actual = digest(target)
            if expected and actual != expected:
                raise SystemExit(f"Checksum mismatch, refusing overwrite: {asset['id']}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_suffix(target.suffix + ".part")
            print(f"Downloading {asset['id']}", flush=True)
            if asset.get("archive_member"):
                archive_path = ROOT / ".local/downloads/buffalo_l.zip"
                if not archive_path.exists():
                    archive_partial = archive_path.with_suffix(".zip.part")
                    download(asset["url"], archive_partial)
                    archive_partial.replace(archive_path)
                with zipfile.ZipFile(archive_path) as archive:
                    matches = [n for n in archive.namelist()
                               if Path(n).name == asset["archive_member"]]
                    if len(matches) != 1:
                        raise RuntimeError("Expected exactly one recognition model")
                    with archive.open(matches[0]) as source, partial.open("wb") as out:
                        shutil.copyfileobj(source, out)
            else:
                download(asset["url"], partial)
            actual = digest(partial)
            if expected and actual != expected:
                raise SystemExit(f"Checksum mismatch: {asset['id']}; partial retained")
            partial.replace(target)
        if not expected:
            asset["sha256"] = actual
            asset["size_bytes"] = target.stat().st_size
        print(f"Verified {asset['id']}: {actual}", flush=True)
    if args.record_initial_hashes:
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
