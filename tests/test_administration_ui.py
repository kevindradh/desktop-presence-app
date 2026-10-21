"""Native/offscreen Stage 5 acceptance using real isolated PostgreSQL data."""
from datetime import date
import os
from pathlib import Path

import pytest
from PyQt6.QtCore import QDate, QTime, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from app.models.entities import Role
from tests.test_administration import data, photo
from tests.test_auth import auth, add_role, NEW
from tests.test_database import store
from tests.test_session_ui import views, sign_in, activate

pytestmark = pytest.mark.database


def settled(view, wait_until):
    wait_until(lambda: not view.jobs.tasks.busy and (not view.shell or
        all(not page.pending for page in view.shell.administrative_pages.values())), timeout=10000)


def open_page(view, route, wait_until):
    view.navigate(route)
    settled(view, wait_until)
    return view.shell.administrative_pages[route]


def snapshot(view, name):
    destination = os.environ.get("STARGATE_ADMIN_EVIDENCE")
    if destination:
        folder = Path(destination)
        folder.mkdir(parents=True, exist_ok=True)
        assert view.grab().save(str(folder / name))


def answer(page, button, wait_until):
    wait_until(lambda: any(box.isVisible() for box in page.findChildren(QMessageBox)))
    dialog = next(box for box in page.findChildren(QMessageBox) if box.isVisible())
    dialog.button(button).click()


def test_groups_form_required_create_edit_cancel_delete_and_referenced(auth, data, views, wait_until):
    service, _, _ = auth
    view = views(service)
    sign_in(view, "root", NEW, wait_until)
    page = open_page(view, "groups", wait_until)
    assert page.table.rowCount() == 2
    assert not page.save_button.isEnabled()
    page.name.setText("Grup UI")
    page.description.setText("Contoh")
    page.save_button.click()
    settled(view, wait_until)
    assert page.table.rowCount() == 3
    page.table.selectRow(next(i for i, row in enumerate(page.rows) if row.name == "Grup UI"))
    page.name.setText("Grup UI Edit")
    page.save()
    settled(view, wait_until)
    page.table.selectRow(next(i for i, row in enumerate(page.rows) if row.name == "Grup UI Edit"))
    page.delete()
    answer(page, QMessageBox.StandardButton.No, wait_until)
    assert page.table.rowCount() == 3
    page.delete()
    answer(page, QMessageBox.StandardButton.Yes, wait_until)
    settled(view, wait_until)
    assert page.table.rowCount() == 2
    page.table.selectRow(0)
    page.delete()
    answer(page, QMessageBox.StandardButton.Yes, wait_until)
    settled(view, wait_until)
    assert "digunakan" in page.message.text()
    snapshot(view, "stage-05-groups.png")
    page.refresh_button.click()
    settled(view, wait_until)
    assert page.selected is None and not page.name.text()


def test_shift_form_night_grace_validation_edit_and_delete(auth, data, views, wait_until):
    service, _, _ = auth
    view = views(service)
    sign_in(view, "root", NEW, wait_until)
    page = open_page(view, "shifts", wait_until)
    page.name.setText("Malam UI")
    page.start.setTime(QTime(20, 0))
    page.end.setTime(QTime(4, 0))
    assert "berikutnya" in page.note.text()
    page.grace.setValue(480)
    assert not page.save_button.isEnabled()
    page.grace.setValue(10)
    page.save_button.click()
    settled(view, wait_until)
    assert page.table.rowCount() == 2
    page.table.selectRow(next(i for i, row in enumerate(page.rows) if row.name == "Malam UI"))
    page.name.setText("Malam UI Edit")
    page.save()
    settled(view, wait_until)
    snapshot(view, "stage-05-shifts.png")
    page.table.selectRow(next(i for i, row in enumerate(page.rows) if row.name == "Malam UI Edit"))
    page.delete()
    answer(page, QMessageBox.StandardButton.Yes, wait_until)
    settled(view, wait_until)
    assert page.table.rowCount() == 1
    page.table.selectRow(0)
    page.start.setTime(QTime(21, 0))
    page.save()
    settled(view, wait_until)
    assert "direferensikan" in page.message.text()


def test_member_pagination_search_filter_details_edit_photo_and_registration_gate(auth, data, photo, views, wait_until, monkeypatch):
    service, _, _ = auth
    view = views(service)
    sign_in(view, "root", NEW, wait_until)
    page = open_page(view, "members", wait_until)
    assert page.table.rowCount() == 10 and "25 anggota" in page.page_label.text()
    for width,height in ((1000,740),(1180,820),(1440,900)):
        view.resize(width,height)
        QTest.qWait(50)
        for left,right in ((page.code,page.name),(page.group,page.position),(page.email,page.phone)):
            assert left.y()==right.y() and left.geometry().right()<right.x()
            assert page.form_widget.rect().contains(left.geometry())
            assert page.form_widget.rect().contains(right.geometry())
        assert view.shell.pages.currentWidget().horizontalScrollBar().maximum()==0
    activate(view)
    page.code.setFocus()
    wait_until(page.code.hasFocus)
    for previous,current in ((page.code,page.name),(page.name,page.group),
                             (page.group,page.position),(page.position,page.email),(page.email,page.phone)):
        QTest.keyClick(previous,Qt.Key.Key_Tab)
        assert current.hasFocus()
    snapshot(view, "stage-05-members.png")
    page.next_button.click()
    settled(view, wait_until)
    assert page.offset == 10
    page.next_button.click()
    settled(view, wait_until)
    assert page.offset == 20 and page.table.rowCount() == 5 and not page.next_button.isEnabled()
    page.previous_button.click()
    settled(view, wait_until)
    assert page.offset == 10
    page.search.setText("Anggota Uji 01")
    page.filter_changed()
    settled(view, wait_until)
    assert page.table.rowCount() == 1
    page.search.clear()
    page.filter_changed()
    settled(view, wait_until)
    page.group_filter.setCurrentIndex(page.group_filter.findData(data[2]))
    settled(view, wait_until)
    assert page.total == 12
    page.group_filter.setCurrentIndex(0)
    settled(view, wait_until)
    page.table.selectRow(0)
    settled(view, wait_until)
    assert page.selected.id == data[0] and page.history.rowCount() == 1
    page.name.clear()
    assert not page.save_button.isEnabled()
    page.name.setText("Edit UI Unicode 李")
    page.group.setCurrentIndex(page.group.findData(data[2]))
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(photo), ""))
    page.choose_photo()
    assert page.photo_source == str(photo)
    page.save()
    settled(view, wait_until)
    page.table.selectRow(0)
    settled(view, wait_until)
    assert page.name.text() == "Edit UI Unicode 李" and page.group.currentData() == data[2]
    assert page.history.item(0,4).text() == "Kelas Uji"
    assert page.preview.parentWidget().rect().contains(page.preview.geometry())
    assert page.photo_button.parentWidget().rect().contains(page.photo_button.geometry())
    assert page.form_widget.rect().contains(page.preview.parentWidget().geometry())
    snapshot(view, "stage-05-member-detail.png")
    page.new_button.click()
    page.code.setText("NEW")
    page.name.setText("Baru")
    page.group.setCurrentIndex(page.group.findData(data[1]))
    assert not page.photo_button.isEnabled()
    assert page.selected is None and not page.save_button.isEnabled() and page.capture_button.isEnabled()
    assert view.administration.members(view.login.token).total == 25


def test_member_deactivate_confirmation_and_history_preserved(auth, data, views, wait_until):
    service, _, _ = auth
    view = views(service)
    sign_in(view, "root", NEW, wait_until)
    page = open_page(view, "members", wait_until)
    page.table.selectRow(0)
    settled(view, wait_until)
    page.deactivate()
    answer(page, QMessageBox.StandardButton.No, wait_until)
    assert page.selected.active
    page.deactivate()
    answer(page, QMessageBox.StandardButton.Yes, wait_until)
    settled(view, wait_until)
    assert page.total == 24
    page.status_filter.setCurrentIndex(page.status_filter.findData(False))
    settled(view, wait_until)
    assert page.total == 1
    page.table.selectRow(0)
    settled(view, wait_until)
    assert not page.selected.active and page.history.rowCount() == 1
    assert not page.deactivate_button.isEnabled()


def test_member_shift_assignment_open_end_and_next_day(auth, data, views, wait_until):
    service, _, _ = auth
    view = views(service)
    sign_in(view, "root", NEW, wait_until)
    page = open_page(view, "members", wait_until)
    page.table.selectRow(0)
    settled(view, wait_until)
    tab_bar=page.member_tabs.tabBar()
    QTest.mouseClick(tab_bar,Qt.MouseButton.LeftButton,pos=tab_bar.tabRect(1).center())
    assert page.member_tabs.currentWidget() is page.shift_tab
    assert page.assignment_widget.isVisible() and not page.form_widget.isVisible()
    assert not page.assign_button.isEnabled()
    page.shift.setCurrentIndex(page.shift.findData(data[3]))
    assert page.assign_button.isEnabled()
    page.starts.setDate(QDate(2026,10,1))
    page.assign_button.click()
    settled(view, wait_until)
    assert page.assignment_table.rowCount() == 1
    assert not page.end_assignment_button.isEnabled()
    page.existing_assignment.setCurrentIndex(1)
    assert page.end_assignment_button.isEnabled()
    page.existing_assignment.setCurrentIndex(0)
    assert not page.end_assignment_button.isEnabled()
    page.existing_assignment.setCurrentIndex(1)
    assert page.end_assignment_button.isEnabled()
    page.end_existing_date.setDate(QDate(2026,10,18))
    page.end_assignment_button.click()
    settled(view, wait_until)
    assert page.assignment_table.item(0,2).text() == "2026-10-18"
    page.shift.setCurrentIndex(page.shift.findData(data[3]))
    page.starts.setDate(QDate(2026,10,19))
    page.unlimited.setChecked(False)
    page.ends.setDate(QDate(2026,10,31))
    assert page.assign_button.isEnabled()
    page.assign_button.click()
    settled(view, wait_until)
    assert page.assignment_table.rowCount() == 2
    assert page.member_tabs.currentWidget() is page.shift_tab
    assert view.shell.pages.currentWidget().horizontalScrollBar().maximum()==0
    snapshot(view,'members-shift-tab.png')


def test_operator_can_edit_members_but_cannot_assign_shift(auth, data, views, wait_until):
    service, admin, _ = auth
    _, login = add_role(service, admin, Role.OPERATOR)
    view = views(service)
    sign_in(view, login.principal.username, NEW, wait_until)
    assert "groups" not in view.shell.administrative_pages and "shifts" not in view.shell.administrative_pages
    page = open_page(view, "members", wait_until)
    page.table.selectRow(0)
    settled(view, wait_until)
    page.member_tabs.setCurrentWidget(page.shift_tab)
    assert not page.assignment_widget.isVisible()
    assert not page.assign_button.isEnabled()
    page.member_tabs.setCurrentWidget(page.data_tab)
    page.name.setText("Edit oleh Operator")
    page.save()
    settled(view, wait_until)
    assert view.administration.member(view.login.token, data[0]).member.name == "Edit oleh Operator"


def test_member_tabs_keep_selection_and_draft_and_support_keyboard(auth,data,views,wait_until):
    service,_,_=auth
    view=views(service)
    sign_in(view,'root',NEW,wait_until)
    page=open_page(view,'members',wait_until)
    assert page.member_tabs.count()==2
    assert page.member_tabs.currentWidget() is page.data_tab
    page.table.selectRow(0)
    settled(view,wait_until)
    selected=page.selected.id
    page.name.setText('Draf nama anggota')
    bar=page.member_tabs.tabBar()
    QTest.mouseClick(bar,Qt.MouseButton.LeftButton,pos=bar.tabRect(1).center())
    assert page.member_tabs.currentWidget() is page.shift_tab
    assert page.selected.id==selected and page.name.text()=='Draf nama anggota'
    activate(view)
    bar.setFocus()
    QTest.keyClick(bar,Qt.Key.Key_Tab,Qt.KeyboardModifier.ControlModifier)
    assert page.member_tabs.currentWidget() is page.data_tab
    assert page.selected.id==selected and page.name.text()=='Draf nama anggota'
    page.member_tabs.setCurrentWidget(page.shift_tab)
    page.table.selectRow(1)
    settled(view,wait_until)
    assert page.selected.id!=selected and page.member_tabs.currentWidget() is page.shift_tab
    page.member_tabs.setCurrentWidget(page.data_tab)
    page.new_button.click()
    assert page.selected is None and page.member_tabs.currentWidget() is page.data_tab
    page.member_tabs.setCurrentWidget(page.shift_tab)
    assert page.assignment_message.isVisible() and not page.assignment_widget.isVisible()


def test_administration_search_typing_survives_periodic_checks(auth, data, views, wait_until):
    service, _, _ = auth
    view = views(service)
    sign_in(view, "root", NEW, wait_until)
    page = open_page(view, "members", wait_until)
    activate(view)
    page.search.setFocus()
    wait_until(page.search.hasFocus)
    QTest.keyClicks(page.search, "Anggota")
    page.filter_changed()
    settled(view, wait_until)
    view._check_session()
    settled(view, wait_until)
    assert page.search.hasFocus() and page.search.text() == "Anggota"
    QTest.keyClicks(page.search, " Uji")
    assert page.search.text() == "Anggota Uji"
