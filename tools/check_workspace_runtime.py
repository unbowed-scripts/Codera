"""Opt-in network check: download Python and prepare a disposable Web project."""
import os
import sys
import tempfile
import time
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from backend import Backend
from curriculum import TRACKS


def main():
    app = QGuiApplication([])
    with tempfile.TemporaryDirectory() as folder:
        backend = Backend(QSettings(folder + '/settings.ini', QSettings.IniFormat))
        workspace = backend.workspace
        runtime = workspace.runtime
        runtime.install_dir = Path(folder) / 'python'
        def wait(predicate, seconds=180):
            deadline = time.monotonic() + seconds
            while not predicate() and time.monotonic() < deadline: QTest.qWait(50)
            assert predicate(), 'Timeout: ' + runtime.status
        try:
            runtime.downloadPython()
            wait(lambda: not runtime.busy)
            assert Path(runtime.python).is_relative_to(folder), runtime.status + '\n' + runtime.log
            print('Python download and discovery passed', flush=True)
            workspace.configure(folder + '/projects', '', '', '[]')
            backend.open('lesson', TRACKS['Web'][0].id + '/1')
            workspace.open('practice')
            workspace.prepare()
            wait(lambda: not runtime.busy)
            print(runtime.status, runtime.log, flush=True)
            workspace.content = 'import flask, requests, pip, sys\nprint("WEB-ENV-OK", sys.version_info[:2])\n'
            workspace.runFile()
            wait(lambda: not workspace.terminal.running, 15)
            assert 'WEB-ENV-OK' in workspace.terminal.text, workspace.terminal.text
            assert 'Traceback' not in workspace.terminal.text, workspace.terminal.text
            print('Isolated Web environment and script execution passed', flush=True)
        finally:
            workspace.shutdown()

if __name__ == '__main__': main()
