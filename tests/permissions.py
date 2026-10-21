"""Assert effective platform permissions, using independent Windows ACL inspection."""
import base64
import json
import os
from pathlib import Path
import subprocess


def assert_private_path(path, *, directory=False):
    path = Path(path)
    if os.name != 'nt':
        assert path.stat().st_mode & 0o777 == (0o700 if directory else 0o600)
        return
    script = '''$ErrorActionPreference='Stop'
$acl=Get-Acl -LiteralPath $env:STARGATE_TEST_PRIVATE_PATH
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$entries=@($acl.Access | ForEach-Object {
 [ordered]@{sid=$_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value;
 type=$_.AccessControlType.ToString(); rights=[int]$_.FileSystemRights; inherited=$_.IsInherited}
})
@{protected=$acl.AreAccessRulesProtected; user=$sid; entries=$entries} | ConvertTo-Json -Depth 4
'''
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                            capture_output=True, text=True, check=True, timeout=30,
                            env=dict(os.environ, STARGATE_TEST_PRIVATE_PATH=str(path)))
    acl = json.loads(result.stdout)
    assert acl['protected']
    assert len(acl['entries']) == 2
    assert {e['sid'] for e in acl['entries']} == {acl['user'], 'S-1-5-18'}
    assert all(e['type'] == 'Allow' and e['rights'] & 0x1f01ff == 0x1f01ff
               and not e['inherited'] for e in acl['entries'])
