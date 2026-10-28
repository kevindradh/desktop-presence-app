import hashlib
import json

import pytest
from scripts import setup_source_windows as setup


@pytest.fixture
def source_support(tmp_path,monkeypatch):
    files={}
    for name in ('wheelhouse/demo.whl','postgresql/runtime-manifest.json',
                 'resources/models/demo.onnx','third_party/minifasnet/LICENSE',
                 'third_party/minifasnet/MiniFASNet.py'):
        path=tmp_path/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(b'synthetic support fixture')
        files[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path/'source-support-manifest.json').write_text(json.dumps({'files':files}))
    monkeypatch.setattr(setup,'ROOT',tmp_path)
    return tmp_path


def test_declared_model_source_and_license_are_verified(source_support):
    assert setup.verify_support()==5


def test_modified_model_stops_setup(source_support):
    (source_support/'resources/models/demo.onnx').write_bytes(b'changed model')
    with pytest.raises(ValueError,match='berubah'):setup.verify_support()


def test_extra_runtime_file_stops_setup(source_support):
    (source_support/'postgresql/unexpected.dll').write_bytes(b'unknown')
    with pytest.raises(ValueError,match='bertambah'):setup.verify_support()


def test_manifest_cannot_read_outside_source_folder(tmp_path,monkeypatch):
    (tmp_path/'source-support-manifest.json').write_text(json.dumps({'files':{'../private':'0'*64}}))
    monkeypatch.setattr(setup,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='tidak valid'):setup.verify_support()
