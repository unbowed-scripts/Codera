"""PythonTech desktop entry point: Qt Quick/QML UI with a Python learning model."""
import os
import sys
from pathlib import Path

VERSION = '0.2.0'
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
    model = Backend()
    engine = create_engine(model)
    if not engine.rootObjects():
        return 1
    result = app.exec()
    # Destroy QML while its backend is still alive.
    del engine
    return result


if __name__ == '__main__':
    sys.exit(main())
