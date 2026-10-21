"""Console companion: explicit maintenance/probe commands, never migrations at GUI startup."""
if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()

import sys
if not getattr(sys,'frozen',False):
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main(argv=None):
    import sys
    argv=list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {'setup-local','stop-local-db','setup-check'}:
        from scripts.setup_local_windows import main as setup
        return setup(argv)
    if argv and argv[0]=='package-check':
        from app.bootstrap import main as application
        return application(['--package-check',*argv[1:]])
    from scripts.manage_database import main as database
    return database(argv)


if __name__=='__main__':raise SystemExit(main())
