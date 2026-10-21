"""Verify pinned assets before any model parser or pickle loader runs."""
import hashlib
import json
from pathlib import Path
from ai.contracts import ModelError

ASSETS=("retinaface-weights","retinaface-config","arcface-weights","face-landmarks","minifasnet-weights","minifasnet-source")


def verified_assets(root,model_dir):
    try:
        root,model_dir=Path(root),Path(model_dir)
        manifest=json.loads((root/"models/manifest.json").read_text())
        entries={a["id"]:a for a in manifest["assets"]}
        result={}
        for name in ASSETS:
            entry=entries[name]
            path=(root/entry["path"]) if name=="minifasnet-source" else (model_dir/Path(entry["path"]).name)
            with path.open("rb") as stream:
                checksum=hashlib.file_digest(stream,"sha256").hexdigest()
            if checksum!=entry["sha256"]:
                raise ValueError
            result[name]=path
        result["version"]="arcface-r50-106-v1-"+entries["arcface-weights"]["sha256"][:12]+"-"+entries["face-landmarks"]["sha256"][:12]
        return result
    except (OSError,ValueError,KeyError,TypeError):
        raise ModelError() from None
