"""Private profile image copies. No face detection or enrollment occurs here."""
from pathlib import Path
import os
import uuid

from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QSize, Qt
from PyQt6.QtGui import QImageReader

from app.services.database import DataValidationError
from app.services.private_files import restrict_path


class PhotoStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.folder = self.root / ".local" / "member_photos"

    def import_photo(self, source):
        try:
            with Path(source).open("rb") as handle:
                data = handle.read(10 * 1024 * 1024 + 1)
        except (OSError, TypeError, ValueError):
            raise DataValidationError("Foto tidak dapat dibaca. Pilih berkas PNG atau JPEG.") from None
        return self.import_bytes(data)

    def import_bytes(self, data):
        if not isinstance(data, bytes) or not data or len(data) > 10 * 1024 * 1024:
            raise DataValidationError("Ukuran foto harus lebih dari nol dan maksimal 10 MiB.")
        buffer = QBuffer()
        buffer.setData(QByteArray(data))
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        reader = QImageReader(buffer)
        reader.setDecideFormatFromContent(True)
        size = reader.size()
        if bytes(reader.format()).lower() not in {b"png", b"jpeg", b"jpg"} or not size.isValid():
            raise DataValidationError("Foto harus berupa gambar PNG atau JPEG yang valid.")
        if size.width() * size.height() > 16_000_000:
            raise DataValidationError("Resolusi foto terlalu besar; maksimal 16 megapiksel.")
        reader.setAutoTransform(True)
        if max(size.width(), size.height()) > 1024:
            reader.setScaledSize(size.scaled(QSize(1024, 1024), Qt.AspectRatioMode.KeepAspectRatio))
        image = reader.read()
        if image.isNull():
            raise DataValidationError("Foto rusak atau tidak dapat dibaca.")
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        restrict_path(self.folder, directory=True)
        destination = self.folder / (uuid.uuid4().hex + ".png")
        try:
            # Reserve private permissions before writing any image bytes.
            descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(descriptor)
            restrict_path(destination)
            if not image.save(str(destination), "PNG"):
                raise OSError
        except OSError:
            destination.unlink(missing_ok=True)
            raise DataValidationError("Foto tidak dapat disimpan. Periksa akses direktori data.") from None
        return destination.relative_to(self.root).as_posix()

    def discard_uncommitted(self, relative):
        path = (self.root / relative).resolve()
        if path.parent == self.folder.resolve():
            path.unlink(missing_ok=True)

    def discard_after_commit(self, relative):
        try:
            self.discard_uncommitted(relative)
            return True
        except OSError:
            return False

    def cleanup_orphans(self, session):
        from sqlalchemy import select
        from app.models.entities import Member
        referenced=set(session.scalars(select(Member.photo_path)))
        pending=0
        if self.folder.exists():
            for path in self.folder.glob('*.png'):
                relative=path.relative_to(self.root).as_posix()
                if relative not in referenced and not self.discard_after_commit(relative):
                    pending+=1
        return pending
