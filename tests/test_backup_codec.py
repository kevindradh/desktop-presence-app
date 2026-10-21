from tests.permissions import assert_private_path
"""Format boundaries without a database or real private data."""
from pathlib import Path
import pytest
from app.services.backup_codec import MAX_BYTES,MAGIC,unseal,seal,publish
from app.services.database import DataValidationError

PASSWORD='Synthetic-backup-2026!'


@pytest.mark.parametrize('password',['short',None,'é'*129])
def test_password_bounds(password):
    with pytest.raises(DataValidationError):seal({'format':1},password)


@pytest.mark.parametrize('content',[b'',b'not a backup',MAGIC+b'x'*44])
def test_invalid_files_fail_safely(tmp_path,content):
    path=tmp_path/'invalid';path.write_bytes(content)
    with pytest.raises(DataValidationError):unseal(path,PASSWORD)


def test_no_overwrite_and_private_permissions(tmp_path,monkeypatch):
    original=tmp_path/'original';original.write_bytes(b'keep')
    with pytest.raises(DataValidationError):publish(original,b'replacement')
    assert original.read_bytes()==b'keep' and not list(tmp_path.glob('.stargate-backup-*'))
    created=publish(tmp_path/'new',b'encrypted');assert_private_path(created)
    # Python 3.11 Windows has no fchmod; mkstemp still reserves the file.
    import app.services.backup_codec as codec
    monkeypatch.delattr(codec.os,'fchmod',raising=False)
    assert publish(tmp_path/'without-fchmod',b'encrypted').read_bytes()==b'encrypted'


def test_symlink_publication_does_not_replace_target(tmp_path):
    original=tmp_path/'original';original.write_bytes(b'keep')
    link=tmp_path/'link'
    try:link.symlink_to(original)
    except OSError as error:
        if getattr(error,'winerror',None)==1314:
            pytest.skip('Standard Windows account has no symlink creation privilege')
        raise
    with pytest.raises(DataValidationError):publish(link,b'replacement')
    assert original.read_bytes()==b'keep' and not list(tmp_path.glob('.stargate-backup-*'))


def test_encryption_randomized_authenticated_and_no_partial_file(tmp_path):
    one=seal({'safe':'synthetic'},PASSWORD);two=seal({'safe':'synthetic'},PASSWORD)
    assert one!=two and b'synthetic' not in one
    path=publish(tmp_path/'copy',one);assert unseal(path,PASSWORD)=={'safe':'synthetic'}
    path.write_bytes(one[:-1]+bytes([one[-1]^1]))
    with pytest.raises(DataValidationError):unseal(path,PASSWORD)
