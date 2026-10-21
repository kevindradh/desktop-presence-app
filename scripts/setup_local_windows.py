"""Offline setup for the explicitly bundled PostgreSQL runtime."""
import argparse
import json
from pathlib import Path
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup-local', 'stop-local-db', 'setup-check'])
    parser.add_argument('--data-dir', type=Path)
    args = parser.parse_args(argv)
    from app.settings.paths import runtime_paths
    from app.services.local_database import LocalSetupError, setup_local, stop_local, verify_runtime
    paths = runtime_paths(data_dir=args.data_dir)
    try:
        if args.action == 'setup-local':
            result = setup_local(paths.data, paths.resources)
        elif args.action == 'stop-local-db':
            stop_local(paths.data, paths.resources)
            result = {'stopped': True}
        else:
            verify_runtime(paths.resources)
            result = {'runtime': 'verified', 'database_changed': False}
        print(json.dumps(result))
        return 0
    except LocalSetupError as error:
        print(str(error), file=sys.stderr)
    except Exception:
        print('Setup lokal gagal. Data tetap disimpan; periksa instalasi dan ruang disk.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
