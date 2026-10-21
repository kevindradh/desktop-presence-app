import os
import subprocess

import pytest
from app.services.private_files import restrict_path
from tests.permissions import assert_private_path


def test_private_file_and_directory_permissions(tmp_path):
    folder = tmp_path / 'private'
    folder.mkdir()
    restrict_path(folder, directory=True)
    assert_private_path(folder, directory=True)
    file = folder / 'private.txt'
    file.write_text('synthetic')
    restrict_path(file)
    assert_private_path(file)


@pytest.mark.skipif(os.name != 'nt', reason='Windows native protected DACL')
def test_windows_private_acl_removes_explicit_everyone_grant(tmp_path):
    file = tmp_path / 'public-before.txt'
    file.write_text('synthetic')
    subprocess.run(['icacls', str(file), '/grant', '*S-1-1-0:R'],
                   capture_output=True, check=True)
    restrict_path(file)
    assert_private_path(file)
