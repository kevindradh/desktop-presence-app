"""Unequal chart row counts must not stretch the heading or legend vertically."""
import logging
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.pages.dashboard import DashboardPage
from app.services.dashboard import ChartRow
from app.services.errors import ErrorReporter
from app.ui.theme import apply_theme


@pytest.mark.parametrize('width',[740,900,1200])
def test_unequal_chart_rows_keep_header_and_legend_compact(qt_app,width):
    logger=logging.Logger('chart-layout-test')
    logger.addHandler(logging.NullHandler())
    controller=SimpleNamespace(_closing=True,reporter=ErrorReporter(logger))
    apply_theme(qt_app)
    page=DashboardPage(controller)
    page.charts['shifts'].set_rows(tuple(ChartRow(name,present,late) for name,present,late in (
        ('SIM SMP Siswa',36,6),('SIM SMP Guru',6,1),('SIM SMP Tata usaha',1,0))))
    page.charts['groups'].set_rows(tuple(ChartRow(f'Grup simulasi {i+1}',6,1) for i in range(8)))
    page.resize(width,1800)
    page.show()
    try:
        qt_app.processEvents()
        for key in ('shifts','groups'):
            chart=page.charts[key]
            body=chart.parentWidget().layout()
            heading,description,legend=[body.itemAt(i).widget() for i in range(3)]
            assert heading.height()<=heading.sizeHint().height()+2
            assert legend.height()<=legend.sizeHint().height()+2
            for previous,current in ((heading,description),(description,legend),(legend,chart)):
                assert 0<=current.y()-previous.geometry().bottom()<=10
        destination=os.environ.get('STARGATE_CHART_LAYOUT_EVIDENCE')
        if destination:
            folder=Path(destination)
            folder.mkdir(parents=True,exist_ok=True)
            assert page.charts['shifts'].parentWidget().grab().save(str(folder/f'chart-layout-{width}.png'))
    finally:
        page.close()
        page.deleteLater()
        qt_app.processEvents()
