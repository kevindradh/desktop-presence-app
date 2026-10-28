import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from scripts import prepare_research_release as release
from scripts import prepare_windows_kit as kit


@pytest.fixture
def candidate(tmp_path, monkeypatch):
    root = tmp_path / 'project'
    root.mkdir()
    source = root / 'main.py'
    source.write_text('print("demo")\n')
    (root / '.env').write_text('PRIVATE_SENTINEL=do-not-export')
    for name in (*release.DOCUMENTS, 'packaging/THIRD_PARTY_NOTICES.md'):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# Research candidate\n')
    installer = tmp_path / 'installer.exe'
    installer.write_bytes(b'test executable fixture')
    artifact = tmp_path / 'artifact.json'
    artifact.write_text(json.dumps({'version': '0.14.2-research', 'sha256': release.digest(installer),
                                    'bytes': installer.stat().st_size}))
    monkeypatch.setattr(kit, 'selected_files', lambda *a, **kw: [source])
    return root, source, installer, artifact, tmp_path / 'StarGate-0.14.2-research'


def test_release_checksums_and_private_data_exclusion(candidate):
    root, source, installer, artifact, output = candidate
    result = release.build_release(installer, artifact, output, root=root)
    archive = Path(result['archive'])
    assert archive.name == 'StarGate-0.14.2-research.zip'
    assert result['sha256'] == release.digest(archive)
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read('release-manifest.json'))
        for name, expected in manifest['files'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
        assert '.env' not in bundle.namelist()
    with zipfile.ZipFile(output / 'source-code.zip') as sources:
        assert set(sources.namelist()) == {'main.py', 'kit-manifest.json'}
        assert b'PRIVATE_SENTINEL' not in sources.read('main.py')
    assert archive.with_suffix('.zip.sha256').read_text().split()[0] == result['sha256']


def test_reject_modified_installer_before_output(candidate):
    root, _, installer, artifact, output = candidate
    installer.write_bytes(b'tampered executable')
    with pytest.raises(ValueError, match='checksum'):
        release.build_release(installer, artifact, output, root=root)
    assert not output.exists()


def test_reject_private_selected_source(candidate, monkeypatch):
    root, _, installer, artifact, output = candidate
    monkeypatch.setattr(kit, 'selected_files', lambda *a, **kw: [root / '.env'])
    with pytest.raises(ValueError, match='Private'):
        release.build_release(installer, artifact, output, root=root)
    assert not output.exists()


def test_never_overwrite_existing_archive(candidate):
    root, _, installer, artifact, output = candidate
    archive = Path(str(output) + '.zip')
    archive.write_bytes(b'existing artifact')
    with pytest.raises(FileExistsError):
        release.build_release(installer, artifact, output, root=root)
    assert archive.read_bytes() == b'existing artifact'
    assert not output.exists()


def test_reject_linked_document(candidate, tmp_path):
    root, _, installer, artifact, output = candidate
    outside = tmp_path / 'outside.md'
    outside.write_text('private outside document')
    document = root / release.DOCUMENTS[0]
    document.unlink()
    document.symlink_to(outside)
    with pytest.raises(ValueError, match='documents'):
        release.build_release(installer, artifact, output, root=root)
    assert not output.exists()
