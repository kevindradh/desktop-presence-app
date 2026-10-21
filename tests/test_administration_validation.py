from datetime import time
from pathlib import Path

import pytest
from PyQt6.QtGui import QImage, QColor

from app.services.administration import clean, identifier, validate_member, validate_shift
from app.services.database import DataValidationError
from app.services.member_photos import PhotoStore


@pytest.mark.parametrize("arguments", [
    ("", time(8), time(17), 10), ("Pagi", time(8), time(8), 0),
    ("Pagi", time(8), time(9), 60), ("Pagi", time(8), time(9), -1),
    ("Pagi", time(8), time(9), True), ("Pagi", time(8,0,1), time(9), 0),
    ("Pagi", "08:00", time(17), 10),
])
def test_invalid_shift(arguments):
    with pytest.raises(DataValidationError):
        validate_shift(*arguments)


@pytest.mark.parametrize("field,value", [("code",""),("name",""),("group_id",None),
    ("email","invalid"),("phone","x"*41),("position","x"*161),("name","line\nbreak")])
def test_invalid_member_fields(field, value):
    arguments = dict(code="TEST", name="Nama", group_id=1)
    arguments[field] = value
    with pytest.raises(DataValidationError):
        validate_member(**arguments)


def test_member_optional_fields_and_minute_boundaries():
    assert validate_member(" SG ", " Nama ", 1)["email"] == ""
    assert validate_shift("Malam", time(20), time(4), 479)[-1] == 479
    assert validate_shift("Pagi", time(8), time(17), 0)[0] == "Pagi"
    assert clean(None, 10) == ""
    for value in (True, 0, -1, "1"):
        with pytest.raises(DataValidationError):
            identifier(value)


def test_invalid_photo_is_not_imported(tmp_path):
    store = PhotoStore(tmp_path)
    for path in (tmp_path / "missing.png", tmp_path / "bad.png"):
        if path.name == "bad.png":
            path.write_bytes(b"not an image")
        with pytest.raises(DataValidationError):
            store.import_photo(path)
    empty = tmp_path / "empty.png"
    empty.touch()
    with pytest.raises(DataValidationError):
        store.import_photo(empty)
    large = tmp_path / "too-large.png"
    with large.open("wb") as stream:
        stream.truncate(10 * 1024 * 1024 + 1)
    with pytest.raises(DataValidationError):
        store.import_photo(large)
    assert not store.folder.exists()


def test_photo_is_bounded_and_cleanup_cannot_delete_source(tmp_path):
    source = tmp_path / "large-dimensions.png"
    image = QImage(2000, 1000, QImage.Format.Format_RGB32)
    image.fill(QColor("#2d6240"))
    assert image.save(str(source))
    store = PhotoStore(tmp_path)
    path = store.import_photo(source)
    stored = QImage(str(tmp_path / path))
    assert stored.width() == 1024 and stored.height() == 512
    store.discard_uncommitted(source.name)
    assert source.exists()
    store.discard_uncommitted(path)
    assert not (tmp_path / path).exists()
