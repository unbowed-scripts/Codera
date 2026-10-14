"""PythonTech desktop entry point: Qt Quick/QML UI with a Python learning model."""
import os
import sys
from pathlib import Path

VERSION = '0.8.0'
ROOT = Path(__file__).resolve().parent
_terminal_type_registered = False


def ensure_runtime():
    try:
        import PySide6.QtQuick
        import PySide6.QtQuickControls2
    except ImportError:
        # Distribution PySide installations may contain Widgets but omit Quick.
        candidate = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if candidate.exists() and Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
            os.execv(str(candidate), [str(candidate), str(ROOT / 'main.py'), *sys.argv[1:]])
        raise SystemExit('Нужен полный PySide6. Установи зависимости: python -m pip install -r requirements.txt')


def create_engine(backend):
    global _terminal_type_registered
    if not _terminal_type_registered:
        from PySide6.QtQml import qmlRegisterType
        from terminal_surface import TerminalSurface
        qmlRegisterType(TerminalSurface, 'PythonTech.Terminal', 1, 0, 'TerminalSurface')
        _terminal_type_registered = True
    from PySide6.QtQuickControls2 import QQuickStyle
    # Use the same customizable controls in the app and every test platform.
    if QQuickStyle.name() != 'Basic':
        QQuickStyle.setStyle('Basic')
    from PySide6.QtQuick import QQuickWindow  # Register the Python window wrapper.
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtCore import QUrl
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('backend', backend)
    engine.load(QUrl.fromLocalFile(str(ROOT / 'qml' / 'Main.qml')))
    return engine


def main():
    ensure_runtime()
    from PySide6.QtGui import QGuiApplication, QFont, QFontDatabase
    from backend import Backend
    app = QGuiApplication(sys.argv)
    app.setOrganizationName('PythonTech')
    app.setApplicationName('PythonTech')
    app.setApplicationVersion(VERSION)
    font = next((f for f in ['Inter', 'Segoe UI', 'Noto Sans', 'DejaVu Sans'] if f in QFontDatabase.families()), 'Sans Serif')
    app.setFont(QFont(font, 11))
    smoke_settings = None
    smoke_folder = None
    workspace_smoke = '--workspace-smoke-test' in sys.argv
    if '--smoke-test' in sys.argv or workspace_smoke:
        import tempfile
        from PySide6.QtCore import QSettings
        smoke_folder = tempfile.TemporaryDirectory()
        smoke_settings = QSettings(str(Path(smoke_folder.name) / 'state.ini'), QSettings.IniFormat)
    model = Backend(smoke_settings)
    app.aboutToQuit.connect(model.workspace.shutdown)
    smoke_errors = []
    if smoke_folder is not None:
        from PySide6.QtCore import qInstallMessageHandler, QtMsgType
        def record_message(kind, context, message):
            if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
                smoke_errors.append(message)
                if sys.stderr is not None:
                    print(message, file=sys.stderr)
        qInstallMessageHandler(record_message)
    engine = create_engine(model)
    if not engine.rootObjects():
        return 1
    if '--smoke-test' in sys.argv or workspace_smoke:
        # Isolate smoke tests from real user settings and render representative pages.
        from PySide6.QtCore import QTimer, QMetaObject
        def verify_bundle():
            QMetaObject.invokeMethod(engine.rootObjects()[0], 'enterCourse')
            model.open('lesson', 'practice/6')
            model.theme = 'light'
            if workspace_smoke:
                import subprocess
                from runtime_manager import uv_executable
                from credentials import CredentialStore
                try:
                    subprocess.run([uv_executable(), '--version'], check=True, timeout=10, capture_output=True)
                    CredentialStore('smoke-test')._backend()  # Import only; never access secrets.
                    model.workspace.configure(str(Path(smoke_folder.name) / 'projects'), '', '', '[]')
                    assert model.workspace.open('practice')
                    shell = os.environ.get('COMSPEC', 'cmd.exe') if os.name == 'nt' else '/bin/sh'
                    args = [shell, '/C', 'echo BUNDLE-TERMINAL-OK'] if os.name == 'nt' else [shell, '-c', 'printf BUNDLE-TERMINAL-OK']
                    model.workspace.terminal.start(args, model.workspace.project, model.workspace._environment())
                    model.workspace.terminalRequested.emit()
                except Exception as error:
                    smoke_errors.append(str(error))
                    app.exit(1)
                    return
                attempts = [0]
                def verify_terminal():
                    attempts[0] += 1
                    terminal = model.workspace.terminal
                    if terminal.running and attempts[0] < 100:
                        QTimer.singleShot(50, verify_terminal)
                        return
                    success = (not terminal.running and 'BUNDLE-TERMINAL-OK' in terminal.text
                               and model.workspace.terminalWindowOpen)
                    model.workspace.close()
                    app.exit(0 if success and not smoke_errors else 1)
                QTimer.singleShot(50, verify_terminal)
                return
            QTimer.singleShot(200, lambda: app.exit(1 if smoke_errors else 0))
        QTimer.singleShot(100, verify_bundle)
    result = app.exec()
    # Destroy QML while its backend is still alive.
    del engine
    if smoke_folder is not None:
        qInstallMessageHandler(None)
        smoke_folder.cleanup()
    return result


if __name__ == '__main__':
    sys.exit(main())
