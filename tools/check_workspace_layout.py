"""Render editor and separate terminal windows with disposable project files."""
import os
import sys
import tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QObject, QSettings, QMetaObject, Qt, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from backend import Backend
from main import create_engine
from check_mobile_layout import walk


def main():
    app = QGuiApplication.instance() or QGuiApplication([])
    output = ROOT / 'build/workspace-preview'
    output.mkdir(parents=True, exist_ok=True)
    messages = []
    previous = qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    with tempfile.TemporaryDirectory() as folder:
        backend = Backend(QSettings(folder + '/settings.ini', QSettings.IniFormat))
        backend.workspace.configure(folder + '/Projects', '', '', '[]')
        backend.open('lesson', 'start/1')
        backend.reducedMotion = True
        engine = create_engine(backend)
        window = engine.rootObjects()[0]
        window.setWidth(1380); window.setHeight(940)
        window.setProperty('inCourse', True)
        assert backend.workspace.open('practice')
        QTest.qWait(100)
        for width, height in ((1380, 940), (320, 640)):
            window.setWidth(width); window.setHeight(height)
            backend.workspace.requestLaunch(False)
            QTest.qWait(250)
            assert window.grabWindow().save(str(output / f'{width}-python-prompt.png'))
            QMetaObject.invokeMethod(window.findChild(QObject, 'pythonSetupDialog'), 'close')
            QTest.qWait(250)
        window.setWidth(1380); window.setHeight(940)
        from runtime_manager import RuntimeManager
        python = RuntimeManager.project_python(backend.workspace.project)
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        backend.workspace._environment_ready(backend.workspace.project)
        QTest.qWait(100)
        popup = window.findChild(QObject, 'workspaceView')
        terminal_window = window.findChild(QObject, 'terminalWindow')
        def find(name, host=window): return next(i for i in walk(host.contentItem()) if i.objectName() == name)
        editor = find('workspaceEditor')
        editor.forceActiveFocus()
        editor.setProperty('text', 'print("Hello from project")\n')
        assert backend.workspace.content == 'print("Hello from project")\n'
        backend.workspace.save()
        app.clipboard().setText('keep-clipboard')
        button = find('openTerminal')
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, button.mapToScene(button.boundingRect().center()).toPoint())
        QTest.qWait(200)
        assert terminal_window.isVisible() and backend.workspace.terminalWindowOpen
        assert app.clipboard().text() == 'keep-clipboard'
        assert find('terminalSurface', terminal_window).hasActiveFocus()
        backend.workspace.terminal.send('printf "Terminal ready\\n"\r')
        for _ in range(100):
            if 'Terminal ready' in backend.workspace.terminal.text: break
            QTest.qWait(20)
        assert 'Terminal ready' in backend.workspace.terminal.text
        for width, height in ((1380, 940), (800, 760), (360, 800), (320, 640)):
            window.setWidth(width); window.setHeight(height)
            for mode in ('editor', 'tasks', 'setup'):
                popup.setProperty('showTasks', mode == 'tasks' or width >= 800)
                popup.setProperty('setup', mode == 'setup')
                QTest.qWait(80)
                assert window.grabWindow().save(str(output / f'{width}-{mode}.png'))
            terminal_window.setWidth(width); terminal_window.setHeight(height)
            for theme in ('dark', 'light', 'custom'):
                backend.workspace.terminalAppearance.apply('monospace', 18 if theme == 'custom' else 15,
                                                          theme, '#18202c', '#e8edf6', '#ffd166')
                terminal_window.setProperty('tasksVisible', width >= 800)
                QTest.qWait(100)
                surface = find('terminalSurface', terminal_window)
                assert surface.width() > 100 and surface.height() > 100
                assert backend.workspace.terminal.screen.columns == surface._columns
                assert terminal_window.grabWindow().save(str(output / f'{width}-terminal-{theme}.png'))
            drawer = terminal_window.findChild(QObject, 'terminalAppearanceDrawer')
            QMetaObject.invokeMethod(drawer, 'open')
            QTest.qWait(350)
            assert terminal_window.grabWindow().save(str(output / f'{width}-terminal-settings.png'))
            QMetaObject.invokeMethod(drawer, 'close')
            QTest.qWait(350)
        popup.setProperty('setup', False)
        for i in range(len(backend.workspace.tasks)): backend.workspace.checkTask(i, True)
        assert backend.workspace.complete()
        QTest.qWait(200)
        assert backend.routeKey == 'lesson:start/2'
        assert not terminal_window.isVisible()
        backend.workspace.shutdown()
        window.close()
        del engine
    qInstallMessageHandler(previous)
    assert not messages, '\n'.join(messages)
    print('Workspace and separate terminal layouts passed:', output)


if __name__ == '__main__': main()
