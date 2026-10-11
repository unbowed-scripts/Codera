"""PythonTech desktop entry point: Qt Quick/QML UI with a Python learning model."""
import os
import sys
from pathlib import Path

VERSION = '0.3.0'
ROOT = Path(__file__).resolve().parent


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
    from PySide6.QtQuickControls2 import QQuickStyle
    from backend import Backend
    QQuickStyle.setStyle('Basic')
    app = QGuiApplication(sys.argv)
    app.setOrganizationName('PythonTech')
    app.setApplicationName('PythonTech')
    app.setApplicationVersion(VERSION)
    font = next((f for f in ['Inter', 'Segoe UI', 'Noto Sans', 'DejaVu Sans'] if f in QFontDatabase.families()), 'Sans Serif')
    app.setFont(QFont(font, 11))
    smoke_settings = None
    smoke_folder = None
    if '--smoke-test' in sys.argv:
        import tempfile
        from PySide6.QtCore import QSettings
        smoke_folder = tempfile.TemporaryDirectory()
        smoke_settings = QSettings(str(Path(smoke_folder.name) / 'state.ini'), QSettings.IniFormat)
    model = Backend(smoke_settings)
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
    if '--smoke-test' in sys.argv:
        # Isolate smoke tests from real user settings and render representative pages.
        from PySide6.QtCore import QTimer, QMetaObject
        def verify_bundle():
            QMetaObject.invokeMethod(engine.rootObjects()[0], 'enterCourse')
            model.open('lesson', 'practice/6')
            model.theme = 'light'
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
