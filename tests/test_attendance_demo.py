"""Demo uses production services with isolated SQL and synthetic camera workers."""
import logging
from pathlib import Path

import pytest
from PyQt6.QtTest import QTest

from app.services.errors import ErrorReporter
from app.settings.config import load_config
from app.ui.attendance_demo import AttendanceDemo
from app.ui.theme import apply_theme
from database.attendance_demo import SCENARIOS, events, seed_demo
from tests.test_database import store

pytestmark = pytest.mark.database


@pytest.mark.parametrize('index', range(len(SCENARIOS)))
def test_demo_scenario_uses_real_attendance_service(store, tmp_path, index):
    data = seed_demo(store, load_config(tmp_path, environ={}))
    SCENARIOS[index][1](data)


def test_demo_refuses_development_database(tmp_path):
    from types import SimpleNamespace
    from app.settings.config import DatabaseConfig
    with pytest.raises(ValueError, match='database uji'):
        seed_demo(SimpleNamespace(schema='public', config=DatabaseConfig()), load_config(tmp_path, environ={}))


def test_demo_window_runs_scenario_and_interactive_in_out(store, tmp_path, qt_app, wait_until, monkeypatch):
    apply_theme(qt_app)
    config = load_config(tmp_path, environ={})
    data = seed_demo(store, config)
    logger = logging.Logger('demo-test')
    logger.addHandler(logging.NullHandler())
    reporter = ErrorReporter(logger)
    window = AttendanceDemo(config, logger, reporter, data)
    window.show()
    try:
        window.table.selectRow(1)
        window.run_selected.click()
        wait_until(lambda: not window.tasks.busy and 1 in window.results, timeout=20000)
        assert window.results[1]['status'] == 'LULUS'
        # The automatic runner owns another schema; it must not alter this page.
        assert not events(data)
        from PyQt6.QtWidgets import QFileDialog
        report = tmp_path/'demo-results.json'
        monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(report), 'JSON'))
        window.export.click()
        import json
        exported = json.loads(report.read_text())
        assert not exported['real_camera_tested'] and len(exported['results']) == 9
        assert exported['results'][0]['status'] == 'BELUM DIUJI'
        assert exported['results'][1]['status'] == 'LULUS'
        window.run_all.click()
        wait_until(lambda: len(window.results) == 9 and not window.tasks.busy and not window.queue, timeout=45000)
        assert all(result['status'] == 'LULUS' for result in window.results.values())
        assert not events(data)
        window.tabs.setCurrentIndex(1)
        page = window.page
        wait_until(lambda: bool(page.rows) and not page.pending and not window.session.jobs.tasks.busy, timeout=8000)
        page.device.setCurrentIndex(1)
        page.start_button.click()
        # Match the controller's 30s model-start allowance plus the first commit.
        try:wait_until(lambda: page.history.rowCount() == 1, timeout=35000)
        except AssertionError:
            raise AssertionError('Demo attendance did not settle: '+page.message.text()+
                '; models='+str([n.inference.state for n in page.nodes.values()])+
                '; cameras='+str([n.state for n in window.session.cameras.nodes.values()])+
                '; history='+str(page.history.rowCount())) from None
        assert events(data)[0]['event'] == 'IN'
        window.face.setCurrentIndex(3)
        QTest.qWait(1500)
        wait_until(lambda:not page.pending and not window.session.jobs.tasks.busy, timeout=8000)
        window.advance.click()
        assert data.clock.now().minute == 1 and data.clock.now().second == 1
        window.face.setCurrentIndex(0)
        wait_until(lambda: page.history.rowCount() == 2, timeout=10000)
        assert [row['event'] for row in events(data)] == ['IN', 'OUT']
        destination = __import__('os').environ.get('STARGATE_DEMO_EVIDENCE')
        if destination:
            Path(destination).mkdir(parents=True, exist_ok=True)
            assert window.grab().save(str(Path(destination)/'stage-10-demo-interactive.png'))
            window.tabs.setCurrentIndex(0)
            assert window.grab().save(str(Path(destination)/'stage-10-demo-scenarios.png'))
    finally:
        window.close()
        wait_until(lambda: window.session._close_ready and not window.tasks.busy and not window.isVisible(), timeout=12000)
        assert not window.session.cameras.busy and not window.page.busy
        window.deleteLater()
        qt_app.processEvents()
