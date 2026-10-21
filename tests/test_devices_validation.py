import pytest

from app.services.database import DataValidationError
from app.services.devices import validate_rtsp
from app.services.device_secrets import DeviceSecretError,DeviceSecretStore
from app.settings.config import ConfigError,load_config
from tests.test_credentials import MemoryKeyring


@pytest.mark.parametrize("source",["",None,"file:///private","https://example.invalid/","rtsp:///no-host", "rtsp://host:99999/live", "rtsp://host:0/live", "rtsp://host/a b", "rtsp://host/live#fragment", "rtsp://host\\path"])
def test_invalid_rtsp_has_safe_error(source):
    with pytest.raises(DataValidationError) as error:
        validate_rtsp(source)
    assert str(source) not in str(error.value) if source else True


def test_rtsp_display_redacts_credentials_path_query_ipv6():
    assert validate_rtsp("rtsp://user:password@host:8554/secret?token=private")=="rtsp://host:8554/"
    assert validate_rtsp("rtsp://user:password@[::1]:8554/secret")=="rtsp://[::1]:8554/"


@pytest.mark.parametrize("key,value",[("CAMERA_MAX_STREAMS","0"),("CAMERA_MAX_STREAMS","5"),
    ("CAMERA_OPEN_TIMEOUT","0"),("CAMERA_READ_TIMEOUT","nan"),("CAMERA_RECONNECT_ATTEMPTS","4")])
def test_invalid_camera_config(tmp_path,key,value):
    with pytest.raises(ConfigError):
        load_config(tmp_path,environ={"STARGATE_"+key:value})


def test_device_vault_only_native_backend_and_safe_missing_secret(tmp_path,monkeypatch):
    import keyring
    backend=MemoryKeyring()
    monkeypatch.setattr(keyring,"get_keyring",lambda:backend)
    store=DeviceSecretStore(load_config(tmp_path,environ={}))
    with pytest.raises(DeviceSecretError):
        store.write("rtsp://user:password@host/secret")
    assert not backend.entries
    native=DeviceSecretStore(load_config(tmp_path,environ={}),backend=backend)
    with pytest.raises(DeviceSecretError):
        native.read("missing")
    reference=native.write("rtsp://user:password@host/secret")
    assert native.read(reference)=="rtsp://user:password@host/secret"
    assert native.discard(reference) and native.discard(None)
