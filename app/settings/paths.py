"""Separate immutable bundle resources from private, writable application data."""
from dataclasses import dataclass
import os
from pathlib import Path
import sys


@dataclass(frozen=True)
class RuntimePaths:
    resources: Path
    data: Path


def runtime_paths(*, data_dir=None, environ=None, platform=None, frozen=None, bundle=None):
    environ = os.environ if environ is None else environ
    platform = sys.platform if platform is None else platform
    frozen = getattr(sys, 'frozen', False) if frozen is None else frozen
    source = Path(__file__).resolve().parents[2]
    resources = Path(bundle or getattr(sys, '_MEIPASS', source)).resolve() if frozen else source
    if data_dir is not None:
        data = Path(data_dir).expanduser().resolve()
    elif not frozen:
        data = source
    elif platform == 'win32':
        from app.settings.config import ConfigError
        if not environ.get('LOCALAPPDATA'):
            raise ConfigError('LOCALAPPDATA tidak tersedia. Pilih --data-dir yang dapat ditulis.')
        data = Path(environ['LOCALAPPDATA'])/'StarGate'
    elif platform == 'darwin':
        data = Path.home()/'Library/Application Support/StarGate'
    else:
        data = Path(environ.get('XDG_DATA_HOME', Path.home()/'.local/share'))/'StarGate'
    return RuntimePaths(resources, data.resolve())
