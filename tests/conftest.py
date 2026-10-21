import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest


def pytest_addoption(parser):
    parser.addoption("--run-db", action="store_true", help="Run isolated real PostgreSQL integration tests")
    parser.addoption("--run-models", action="store_true", help="Run integration with pinned real neural models")


def pytest_configure(config):
    config.addinivalue_line("markers", "database: real PostgreSQL/pgvector integration")
    config.addinivalue_line("markers", "models: real pinned neural models on generated inputs")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-models"):
        for item in items:
            if "models" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Use --run-models for real neural models"))
    if not config.getoption("--run-db"):
        skip = pytest.mark.skip(reason="Use --run-db for real PostgreSQL integration")
        for item in items:
            if "database" in item.keywords:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def qt_app():
    application = QApplication.instance() or QApplication([])
    application.setQuitOnLastWindowClosed(False)
    yield application
    application.processEvents()


@pytest.fixture
def wait_until(qt_app):
    def wait(predicate, timeout=3000):
        import time
        deadline = time.monotonic() + timeout / 1000
        while time.monotonic() < deadline:
            qt_app.processEvents()
            if predicate():
                return
            QTest.qWait(5)
        raise AssertionError("Condition not reached before timeout")
    return wait

# Real neural weights are an explicit integration layer, separate from synthetic stubs.
