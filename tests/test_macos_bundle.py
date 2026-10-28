import plistlib

import pytest

from scripts.build_package import validate_macos_bundle


@pytest.fixture
def bundle(tmp_path):
    app = tmp_path/'StarGate.app'
    resources = app/'Contents/Resources'
    resources.mkdir(parents=True)
    (resources/'stargate.icns').write_bytes(b'test-icon')
    return app


def write_info(bundle, **overrides):
    info = dict(CFBundleExecutable='StarGate', CFBundlePackageType='APPL',
                CFBundleIconFile='stargate.icns', LSBackgroundOnly=False, LSUIElement=False)
    info.update(overrides)
    with (bundle/'Contents/Info.plist').open('wb') as stream:
        plistlib.dump(info, stream)


def test_foreground_gui_bundle_is_accepted(bundle):
    write_info(bundle)
    validate_macos_bundle(bundle)


@pytest.mark.parametrize('override', [
    {'LSBackgroundOnly': True}, {'LSUIElement': True},
    {'CFBundleExecutable': 'StarGateAdmin'}, {'CFBundleIconFile': 'missing.icns'},
])
def test_background_helper_or_missing_icon_cannot_be_distributed(bundle, override):
    write_info(bundle, **override)
    with pytest.raises(ValueError):
        validate_macos_bundle(bundle)
