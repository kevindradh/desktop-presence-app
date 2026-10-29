from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
BROKEN_STREAM = '''
class BrokenConsole:
    def write(self, value): return len(value)
    def flush(self): raise OSError('invalid inherited console handle')
sys.stdout = BrokenConsole()
'''


def test_broken_console_reproduces_python_shutdown_exit_120():
    result = subprocess.run([sys.executable, '-c', 'import sys\n'+BROKEN_STREAM],
                            cwd=ROOT, capture_output=True, timeout=15)
    assert result.returncode == 120


@pytest.mark.parametrize('inherited', ['normal', 'broken', 'windowed', 'closed_fds'])
def test_worker_silences_python_native_output_and_exits_cleanly(inherited):
    setup = {
        'normal': '', 'broken': BROKEN_STREAM,
        'windowed': 'sys.stdout = sys.stderr = None\n',
        'closed_fds': 'os.close(1); os.close(2)\n',
    }[inherited]
    program = 'import os, sys\n'+setup+'''
from app.services.worker_output import silence_worker_output
silence_worker_output()
print('private-output')
print('private-error', file=sys.stderr)
os.write(1, b'native-private-output')
os.write(2, b'native-private-error')
sys.stdout.flush()
sys.stderr.flush()
'''
    result = subprocess.run([sys.executable, '-c', program], cwd=ROOT,
                            capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == b''
