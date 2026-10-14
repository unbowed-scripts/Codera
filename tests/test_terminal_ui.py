"""Real QQuickWindow clicks/keystrokes, independent of direct terminal.send tests."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen' if os.name != 'nt' else 'windows')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QObject, QSettings, Qt, QPoint, QPointF, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from PySide6.QtTest import QTest
from backend import Backend
from main import create_engine
from terminal_preferences import TerminalPreferences

app = QGuiApplication.instance() or QGuiApplication([])


def walk(item):
    yield item
    for child in item.childItems(): yield from walk(child)


class TerminalUiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.messages = []
        self.handler = qInstallMessageHandler(lambda kind, context, message: self.messages.append(message))
        self.backend = Backend(QSettings(self.temp.name + '/settings.ini', QSettings.IniFormat))
        self.ws = self.backend.workspace
        self.ws.configure(self.temp.name + '/Project space', '', '', '[]')
        self.backend.open('lesson', 'start/1')
        self.engine = create_engine(self.backend)
        self.window = self.engine.rootObjects()[0]
        self.window.setWidth(1200); self.window.setHeight(800)
        self.window.setProperty('inCourse', True)
        self.ws.open('practice')
        from runtime_manager import RuntimeManager
        python = RuntimeManager.project_python(self.ws.project)
        python.parent.mkdir(parents=True)
        python.write_bytes(b'fixture: terminal uses sys.executable directly')
        self.ws._environment_ready(self.ws.project)
        QTest.qWait(100)
        self.terminal_window = self.window.findChild(QObject, 'terminalWindow')

    def tearDown(self):
        self.ws.shutdown()
        self.ws.close()
        self.terminal_window.close()
        self.window.close()
        self.engine.deleteLater()
        QTest.qWait(40)
        qInstallMessageHandler(self.handler)
        self.temp.cleanup()
        self.assertFalse(self.messages, '\n'.join(self.messages))

    def find(self, name, window=None):
        window = window or self.window
        return next(item for item in walk(window.contentItem()) if item.objectName() == name)

    def click(self, name, window=None):
        window = window or self.window
        button = self.find(name, window)
        point = button.mapToScene(button.boundingRect().center()).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
        QTest.qWait(320)

    def wait(self, predicate):
        for _ in range(250):
            if predicate(): return
            QTest.qWait(20)
        self.fail('Terminal timed out: ' + self.ws.status + '\n' + self.ws.terminal.text)

    def type(self, text):
        for char in text:
            QTest.keyClick(self.terminal_window, char)

    def test_first_launch_offers_python_without_starting_terminal(self):
        from runtime_manager import RuntimeManager
        RuntimeManager.project_python(self.ws.project).unlink()
        self.click('openTerminal')
        dialog = self.window.findChild(QObject, 'pythonSetupDialog')
        self.assertTrue(dialog.property('visible'))
        self.assertFalse(self.ws.terminal.running)
        with patch.object(self.ws.runtime, 'download_for_project') as download:
            self.click('installTerminalPython')
            download.assert_called_once_with(self.ws._project, False)
        self.assertFalse(self.ws.terminal.running)

    def test_button_opens_native_window_without_clipboard_or_url(self):
        app.clipboard().setText('clipboard-sentinel')
        with patch('workspace.QDesktopServices.openUrl') as open_url:
            self.click('openTerminal')
            self.assertTrue(self.terminal_window.isVisible())
            self.assertTrue(self.ws.terminalWindowOpen)
            self.assertTrue(self.find('terminalNotice').isVisible())
            self.assertEqual(app.clipboard().text(), 'clipboard-sentinel')
            open_url.assert_not_called()
        self.assertIsNot(self.terminal_window, self.window)
        surface = self.find('terminalSurface', self.terminal_window)
        self.assertTrue(surface.hasActiveFocus())
        self.assertGreater(surface._columns, 50)
        self.assertEqual(surface._columns, self.ws.terminal.screen.columns)
        pid = self.ws.terminal.process.pid
        self.click('openTerminal')
        self.assertEqual(pid, self.ws.terminal.process.pid)
        self.terminal_window.close()
        QTest.qWait(100)
        self.assertFalse(self.ws.terminalWindowOpen)
        self.assertFalse(self.ws.terminal.running)
        self.assertTrue(self.ws.active)

    def test_keyboard_input_ctrl_c_and_click_empty_terminal(self):
        self.click('openTerminal')
        # Use an interactive Python program, preserving the visible terminal window.
        self.ws.terminal.start([sys.executable, '-u', '-c', 'import time; name=input("NAME?"); print("HELLO-"+name); time.sleep(60)'], self.ws.project, self.ws._environment())
        self.wait(lambda: 'NAME?' in self.ws.terminal.text)
        surface = self.find('terminalSurface', self.terminal_window)
        point = surface.mapToScene(QPointF(surface.width() - 30, surface.height() - 30)).toPoint()
        QTest.mouseClick(self.terminal_window, Qt.LeftButton, Qt.NoModifier, point)
        self.assertTrue(surface.hasActiveFocus())
        self.type('Maria')
        QTest.keyClick(self.terminal_window, Qt.Key_Return)
        self.wait(lambda: 'HELLO-Maria' in self.ws.terminal.text)
        QTest.keyClick(self.terminal_window, Qt.Key_C, Qt.ControlModifier)
        self.wait(lambda: not self.ws.terminal.running)
        self.assertIn('KeyboardInterrupt', self.ws.terminal.text)

    def test_unicode_paste_and_appearance_survive_restart(self):
        self.click('openTerminal')
        self.ws.terminal.start([sys.executable, '-u', '-c', 'print("ECHO-"+input("TEXT?"))'], self.ws.project, self.ws._environment())
        self.wait(lambda: 'TEXT?' in self.ws.terminal.text)
        app.clipboard().setText('Привет')
        QTest.keyClick(self.terminal_window, Qt.Key_V, Qt.ControlModifier | Qt.ShiftModifier)
        QTest.keyClick(self.terminal_window, Qt.Key_Return)
        self.wait(lambda: 'ECHO-Привет' in self.ws.terminal.text)
        appearance = self.ws.terminalAppearance
        self.assertTrue(appearance.apply(appearance.fonts[-1], 22, 'custom', '#1a2030', '#f4f6ff', '#ffd166'))
        restored = TerminalPreferences(self.backend.settings)
        self.assertEqual(restored.fontSize, 22)
        self.assertEqual(restored.fontFamily, appearance.fonts[-1])
        self.assertEqual(restored.colors['background'], '#1a2030')
        self.assertFalse(appearance.apply('missing font', 45, 'custom', 'bad', '#ffffff', '#ffffff'))
        self.assertEqual(appearance.fontSize, 22)
        self.assertFalse(appearance.importFont(self.temp.name + '/missing.ttf'))
        self.assertEqual(self.backend.theme, 'green')

    def test_import_font_and_saved_custom_palette(self):
        candidates = [Path('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'), Path('C:/Windows/Fonts/consola.ttf')]
        font = next((path for path in candidates if path.is_file()), None)
        if font is None: self.skipTest('No test font is installed')
        folder = Path(self.temp.name) / 'fonts'
        appearance = TerminalPreferences(self.backend.settings, font_dir=folder)
        self.assertTrue(appearance.importFont(str(font)))
        self.assertTrue(list(folder.glob('*.ttf')))
        self.assertTrue(appearance.apply(appearance.fontFamily, 17, 'custom', '#123456', '#fedcba', '#ffffff'))
        appearance.apply(appearance.fontFamily, 17, 'light', '#ffffff', '#000000', '#000000')
        self.assertEqual(appearance.customColors['background'], '#123456')
        restored = TerminalPreferences(self.backend.settings, font_dir=folder)
        self.assertEqual(restored.fontFamily, appearance.fontFamily)
        self.assertEqual(restored.customColors['background'], '#123456')

    def test_appearance_controls_and_completion(self):
        self.click('openTerminal')
        self.click('terminalAppearanceButton', self.terminal_window)
        self.assertTrue(self.terminal_window.findChild(QObject, 'terminalAppearanceDrawer').property('opened'))
        combo = self.find('terminalTheme', self.terminal_window)
        combo.forceActiveFocus()
        QTest.keyClick(self.terminal_window, Qt.Key_Down)
        QTest.qWait(80)
        self.assertEqual(self.ws.terminalAppearance.theme, 'light')
        surface = self.find('terminalSurface', self.terminal_window)
        self.assertEqual(surface.appearance.colors['background'], '#ffffff')
        drawer = self.terminal_window.findChild(QObject, 'terminalAppearanceDrawer')
        from PySide6.QtCore import QMetaObject
        QMetaObject.invokeMethod(drawer, 'close')
        QTest.qWait(320)
        for index in range(len(self.ws.tasks)): self.ws.checkTask(index, True)
        self.click('terminalComplete', self.terminal_window)
        QTest.qWait(200)
        self.assertEqual(self.backend.routeKey, 'lesson:start/2')
        self.assertFalse(self.terminal_window.isVisible())
