"""Build-only frozen UI proof restricted to the SGAuto28 synthetic profile."""
import multiprocessing
multiprocessing.freeze_support()
import ctypes
import getpass
import json
import os
from pathlib import Path
import secrets
import sys
import time


def main():
    assert getattr(sys,'frozen',False), 'Only the build-only frozen companion is permitted'
    if getpass.getuser().lower()!='sgauto28' or ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError('Only the owned standard UAT account is permitted')
    from app.settings.paths import runtime_paths
    from app.settings.config import load_config
    from app.services.database import Database,create_database_engine
    from app.services.auth import AuthService
    from app.services.credential_store import CredentialStore
    from app.services.local_database import ensure_local_database,write_new
    from app.models.entities import User,Member,Attendance
    from sqlalchemy import select,func,text
    paths=runtime_paths()
    config=load_config(paths.data,bundle_root=paths.resources)
    assert 'sgauto28' in str(config.root).lower() and config.database.name=='stargate_local'
    assert (config.root/'.local/managed-postgres/state.json').is_file()
    ensure_local_database(config)
    database=Database(create_database_engine(config.database))
    auth=AuthService(database)
    credentials=CredentialStore(config)
    evidence=Path(os.environ['LOCALAPPDATA'])/'StarGate-UAT28'
    phase=sys.argv[1]
    try:
        if phase=='resume':
            token=credentials.get();assert token
            login=auth.resume(token)
            assert auth.authorize(login.token,'backup')
            auth.logout(login.token);credentials.clear()
            print(json.dumps({'native_credential_across_processes':True}))
            return 0
        if phase=='inspect':
            with database.transaction() as session:
                counts={model.__tablename__:session.scalar(select(func.count()).select_from(model)) for model in (User,Member,Attendance)}
                role=session.execute(text('SELECT current_user, rolsuper FROM pg_roles WHERE rolname=current_user')).one()
                vector=session.scalar(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
                listener=session.scalar(text('SHOW listen_addresses'))
            assert counts['members']==80 and counts['users']==5
            baseline=json.loads((evidence/'frozen-ui.json').read_text(encoding='utf-8'))
            assert counts['attendance']==baseline['school_seed']['attendance_events']
            assert role[0]=='stargate_app' and not role[1] and vector=='0.8.7' and listener=='127.0.0.1'
            print(json.dumps({'preserved_counts':counts,'application_role':role[0],
                'application_superuser':role[1],'vector':vector,'listener':listener}))
            return 0
        assert phase=='initialize'
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QFont,QFontDatabase,QRawFont
        from app.ui.session_window import SessionWindow
        from app.ui.theme import apply_theme
        from app.services.errors import ErrorReporter
        from app.services.diagnostic_logging import configure_logging
        from database.seed.school import seed_school
        app=QApplication([])
        for name in ('segoeui.ttf','segoeuib.ttf'):
            assert QFontDatabase.addApplicationFont(str(Path(os.environ['SystemRoot'])/'Fonts'/name))>=0
        apply_theme(app)
        app.setFont(QFont('Segoe UI',10))
        assert QRawFont.fromFont(app.font()).supportsCharacter('A')
        logger=configure_logging(config.log_dir,config.log_level,config.secrets)
        view=SessionWindow(config,logger,ErrorReporter(logger),auth,credentials)
        view.show()
        def wait(predicate,timeout=30):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                app.processEvents()
                if predicate():return
                time.sleep(.01)
            raise AssertionError('Frozen UAT window did not settle: '+view.error_message.text())
        wait(lambda:not view.jobs.tasks.busy and view._entry_state in {'setup','login'})
        file=config.root/'.local/automatic-uat-account.json'
        if not file.exists():
            assert auth.bootstrap_required()
            password=secrets.token_urlsafe(24)+'aA1!'
            write_new(file,json.dumps({'password':password}))
            view.setup_username.setText('auto-uat-admin')
            view.setup_fullname.setText('Penguji Sintetis Windows')
            view.setup_password.setText(password);view.setup_confirm.setText(password)
            view.setup_submit.click()
            wait(lambda:view._entry_state=='login' and not view.jobs.tasks.busy)
        password=json.loads(file.read_text())['password']
        view.username.setText('auto-uat-admin');view.password.setText(password)
        view.signin_button.click()
        wait(lambda:view.shell is not None and not view.jobs.tasks.busy)
        assert not view.login.principal.must_change_password
        with database.transaction() as session:summary=seed_school(session)
        view.navigate('dashboard')
        page=view.shell.administrative_pages['dashboard']
        wait(lambda:not view.jobs.tasks.busy and not page.busy and page.counters['registered'].text()=='74')
        assert view.grab().save(str(evidence/'frozen-dashboard.png'))
        view._message('Notifikasi uji sementara')
        assert view.toast.isVisible()
        assert view.grab().save(str(evidence/'frozen-toast.png'))
        wait(lambda:not view.toast.isVisible(),timeout=10)
        grant=auth.remember(view.login.token);credentials.set(grant.token)
        assert credentials.get()==grant.token
        result={'frozen_gui_bootstrap_login':True,'password_change_optional':True,
            'school_seed':summary,'toast_expired':True,'native_credential_written':True}
        (evidence/'frozen-ui.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result))
        view.close();wait(lambda:not view.isVisible() and not view.jobs.tasks.busy)
        return 0
    finally:database.close()


if __name__=='__main__':raise SystemExit(main())
