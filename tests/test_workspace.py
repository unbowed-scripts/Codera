import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from backend import Backend
from runtime_manager import RuntimeManager
from credentials import CredentialStore

app = QGuiApplication.instance() or QGuiApplication([])


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.b = Backend(QSettings(self.temp.name + '/settings.ini', QSettings.IniFormat))
        self.w = self.b.workspace
        self.assertTrue(self.w.configure(self.temp.name + '/projects with spaces', '', '', '[]'))
        self.b.open('lesson', 'start/1')

    def tearDown(self):
        self.w.shutdown()
        self.b.deleteLater()
        QTest.qWait(10)
        self.temp.cleanup()

    def wait(self, condition, timeout=10000):
        for _ in range(timeout // 20):
            if condition(): return
            QTest.qWait(20)
        self.fail('Operation did not finish: ' + self.w.runtime.status + '\n' + self.w.runtime.log)

    def test_files_conflicts_and_reopen(self):
        self.assertTrue(self.w.open('practice'))
        self.w.content = 'print("Привет")\n'
        self.assertTrue(self.w.save())
        self.assertEqual((Path(self.w.project) / 'main.py').read_text(), self.w.content)
        self.assertTrue(self.w.createFile('templates/index.html'))
        self.w.content = '<h1>Привет</h1>'
        self.assertTrue(self.w.selectFile('main.py'))
        self.w.content = 'print(2)'
        path = Path(self.w.project) / 'main.py'
        path.write_text('print(3)')
        self.assertFalse(self.w.save())
        self.assertFalse(self.w.close())
        self.assertEqual(path.read_text(), 'print(3)')
        self.w.reloadFile()
        self.assertEqual(self.w.content, 'print(3)')
        self.assertTrue(self.w.close())
        self.assertTrue(self.w.open('practice'))
        self.assertEqual(self.w.content, 'print(3)')
        self.assertFalse(self.w.createFile('main.py'))
        self.assertEqual(path.read_text(), 'print(3)')

    def test_paths_and_binary_limits(self):
        self.w.open('practice')
        for name in ('../escape.py', '/tmp/escape.py', '.venv/config.py', '.git/config'):
            self.assertFalse(self.w.createFile(name), name)
        if os.name != 'nt':
            (Path(self.w.project) / 'link').symlink_to(self.temp.name, target_is_directory=True)
            self.assertFalse(self.w.createFile('link/escape.py'))
        (Path(self.w.project) / 'binary').write_bytes(b'\0\xff')
        self.assertFalse(self.w.selectFile('binary'))
        (Path(self.w.project) / 'large').write_bytes(b'a' * (1024 * 1024 + 1))
        self.assertFalse(self.w.selectFile('large'))
        self.assertEqual(self.w.filename, 'main.py')

    def test_manual_progress_and_course_isolation(self):
        destinations = []
        self.w.finished.connect(lambda kind, key: destinations.append((kind, key)))
        self.w.open('practice')
        first = self.w.project
        self.assertFalse(self.w.complete())
        for i in range(len(self.w.tasks)): self.w.checkTask(i, True)
        self.w.close()
        self.w.open('practice')
        self.assertTrue(all(t['done'] for t in self.w.tasks))
        self.assertTrue(self.w.complete())
        self.assertIn('start/1', self.b.practiced)
        self.assertNotIn('start/1', self.b.completed)
        self.assertEqual(destinations, [('lesson', 'start/2')])
        self.b.open('lesson', 'web-start/1')
        # Use a real Web lesson from the catalog, independent of section naming.
        from curriculum import TRACKS
        self.b.open('lesson', TRACKS['Web'][0].id + '/1')
        self.assertTrue(self.w.open('practice'))
        self.assertNotEqual(self.w.project, first)
        self.assertIn('python-web', self.w.project)

    def test_project_gates(self):
        self.b.open('checkpoint', 'start')
        self.assertFalse(self.w.open('project'))
        self.b.completed.update(self.b.section_keys['start'])
        self.b.section_tests.add('start')
        self.assertTrue(self.w.open('project'))
        for i in range(len(self.w.tasks)): self.w.checkTask(i, True)
        self.assertTrue(self.w.complete())
        self.assertIn('start', self.b.section_projects)

    @unittest.skipIf(os.name == 'nt', 'POSIX PTY; ConPTY needs Windows validation')
    def test_real_terminal_input_interrupt_resize_and_restart(self):
        self.w.open('practice')
        terminal = self.w.terminal
        terminal.start([sys.executable, '-u', '-c', 'name=input("NAME?"); print("HELLO-"+name)'], self.w.project, self.w._environment())
        self.wait(lambda: 'NAME?' in terminal.text)
        terminal.send('Мария\r')
        self.wait(lambda: not terminal.running)
        self.assertIn('HELLO-Мария', terminal.text)
        terminal.start([sys.executable, '-u', '-c', 'import time; print("WAIT"); time.sleep(60)'], self.w.project, self.w._environment())
        self.wait(lambda: 'WAIT' in terminal.text)
        terminal.resize(50, 12)
        terminal.interrupt()
        self.wait(lambda: not terminal.running)
        self.assertIn('KeyboardInterrupt', terminal.text)
        self.w.startTerminal()
        terminal.send('printf "SHELL-OK\\n"\r')
        self.wait(lambda: 'SHELL-OK' in terminal.text)
        self.w.close()
        self.assertFalse(terminal.running)
        self.assertIsNone(terminal.process)

    def test_runtime_creates_environment_and_runs_file(self):
        self.w.open('practice')
        self.w.runtime.selectPython(sys.executable)
        self.wait(lambda: not self.w.runtime.busy)
        # Dependency downloads are covered by the opt-in network integration check.
        with patch.object(self.w.runtime, '_install_packages'):
            self.w.prepare()
            self.wait(lambda: not self.w.runtime.busy, 30000)
        self.assertTrue(RuntimeManager.project_python(self.w.project).is_file(), self.w.runtime.log)
        self.w.content = 'print("PROJECT-RUN-OK")'
        self.w.runFile()
        self.wait(lambda: not self.w.terminal.running)
        self.assertIn('PROJECT-RUN-OK', self.w.terminal.text)

    def test_setup_launch_waits_for_success_and_clears_on_failure(self):
        self.w.open('practice')
        runtime = self.w.runtime
        def prepare(*args): runtime._step = 'packages'
        with patch.object(runtime, 'prepare', side_effect=prepare), patch.object(self.w, 'startTerminal') as launch:
            self.w.setupAndLaunch(False, False)
            launch.assert_not_called()
            runtime._step = ''
            runtime.ready.emit(self.w.project)
            launch.assert_called_once()
            runtime.changed.emit()
            self.w.setupAndLaunch(False, False)
            runtime._step = ''
            runtime.changed.emit()  # failure or cancellation must not launch later
            runtime.ready.emit(self.w.project)
            launch.assert_called_once()

    def test_download_chains_preparation_only_after_success(self):
        from PySide6.QtCore import QProcess
        runtime = self.w.runtime
        runtime._step = 'find'
        runtime._output = sys.executable + '\n'
        runtime._prepare_after_download = (self.temp.name, True)
        with patch.object(runtime, '_read'), patch.object(runtime, 'prepare') as prepare:
            runtime._finished(0, QProcess.NormalExit)
            prepare.assert_called_once_with(self.temp.name, True)
        runtime._step = 'find'
        runtime._prepare_after_download = (self.temp.name, True)
        with patch.object(runtime, '_read'), patch.object(runtime, 'prepare') as prepare:
            runtime._finished(1, QProcess.NormalExit)
            prepare.assert_not_called()
        self.assertIsNone(runtime._prepare_after_download)

    def test_runtime_failure_cancel_and_existing_directory(self):
        runtime = self.w.runtime
        runtime.selectPython('/missing/pythontech-python')
        self.assertIn('не найден', runtime.status)
        runtime._run('validate', '/missing/pythontech-python', [])
        self.wait(lambda: not runtime.busy)
        self.assertIn('Не удалось запустить', runtime.status)
        runtime._run('validate', sys.executable, ['-c', 'import time; time.sleep(60)'])
        QTest.qWait(50)
        runtime.cancel()
        self.wait(lambda: not runtime.busy)
        self.assertIn('отменена', runtime.status)
        self.w.open('practice')
        directory = Path(self.w.project) / '.venv'
        directory.mkdir()
        sentinel = directory / 'keep.txt'
        sentinel.write_text('keep')
        self.w.prepare()
        self.assertFalse(runtime.busy)
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assertIn('Переименуй', runtime.status)

    @unittest.skipIf(os.name == 'nt', 'Windows process tree needs native validation')
    def test_close_stops_child_programs(self):
        import psutil
        self.w.open('practice')
        path = Path(self.w.project) / 'pid.txt'
        code = ('import subprocess, sys, time; from pathlib import Path; '
                'p=subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"]); '
                'Path("pid.txt").write_text(str(p.pid)); time.sleep(60)')
        self.w.terminal.start([sys.executable, '-c', code], self.w.project, self.w._environment())
        self.wait(path.exists)
        pid = int(path.read_text())
        self.w.close()
        def stopped():
            try: return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
            except psutil.NoSuchProcess: return True
        self.wait(stopped)

    def test_external_arguments_preserve_paths(self):
        self.w.configure(self.w.root, '', sys.executable, '["-c", "pass", "{project}"]')
        self.w.open('practice')
        with patch('workspace.QProcess') as constructor:
            process = constructor.return_value
            process.startDetached.return_value = (True, 10)
            self.w.openExternal()
            self.assertEqual(process.setArguments.call_args.args[0], ['-c', 'pass', self.w.project])
            self.assertEqual(process.setWorkingDirectory.call_args.args, (self.w.project,))


class CredentialTests(unittest.TestCase):
    def test_native_store_roundtrip_and_no_plaintext_fallback(self):
        store = CredentialStore('test-profile')
        values = {}
        class Vault:
            def set_password(self, service, account, value): values[(service, account)] = value
            def get_password(self, service, account): return values.get((service, account))
            def delete_password(self, service, account): del values[(service, account)]
        with patch.object(store, '_backend', return_value=Vault()):
            store.save('https://example.test/v1', 'model', 'private-key')
            self.assertEqual(store.load('https://example.test/v1', 'model'), 'private-key')
            self.assertEqual(store.load('https://other.test/v1', 'model'), '')
            store.delete('https://example.test/v1', 'model')
            self.assertEqual(values, {})
        with patch.object(store, '_backend', side_effect=RuntimeError('locked')):
            with self.assertRaises(RuntimeError): store.save('u', 'm', 'private-key')

    def test_tutor_persistence_failure_and_forget(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = QSettings(folder + '/state.ini', QSettings.IniFormat)
            b = Backend(settings)
            tutor = b.tutor
            tutor._url, tutor._model, tutor._key = 'https://example.test/v1', 'model', 'private-key'
            tutor._remember = True
            with patch.object(tutor._vault, 'save') as save:
                tutor._save_key()
                save.assert_called_once_with(tutor.url, tutor.model, 'private-key')
            self.assertTrue(tutor.savedKey)
            self.assertNotIn('private-key', Path(settings.fileName()).read_text())
            with patch.object(tutor._vault, 'load', return_value='private-key'), patch.object(tutor, 'connectModel') as connect:
                tutor.connectSaved()
                connect.assert_called_once_with(tutor.url, tutor.model, 'private-key')
            with patch.object(tutor._vault, 'delete', side_effect=RuntimeError()):
                tutor.forgetKey()
            self.assertTrue(tutor.savedKey)
            with patch.object(tutor._vault, 'delete'):
                tutor.forgetKey()
            self.assertFalse(tutor.savedKey)
            tutor._key, tutor._remember = 'private-key', True
            with patch.object(tutor._vault, 'save', side_effect=RuntimeError('private-key')):
                tutor._save_key()
            self.assertIn('только в памяти', tutor.credentialStatus)
            self.assertNotIn('private-key', tutor.credentialStatus)
            self.assertFalse(tutor.savedKey)
            b.workspace.shutdown()
