"""Refresh theme screenshots from the actual QML menu, using isolated settings.
Run from the project root: .venv/bin/python tools/capture_theme_previews.py
"""
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QSettings, QMetaObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from backend import Backend
from main import create_engine


def main():
    app = QGuiApplication([])
    with tempfile.TemporaryDirectory() as folder:
        backend = Backend(QSettings(folder + '/state.ini', QSettings.IniFormat))
        backend.reducedMotion = True
        engine = create_engine(backend)
        window = engine.rootObjects()[0]
        window.setWidth(1200)
        window.setHeight(672)
        QMetaObject.invokeMethod(window, 'enterCourse')
        backend.open('overview', 'Python Core')
        output = ROOT / 'qml' / 'previews'
        output.mkdir(exist_ok=True)
        for theme in backend.themeIds:
            backend.theme = theme
            QTest.qWait(150)
            if not window.grabWindow().save(str(output / (theme + '.png'))):
                raise RuntimeError('Could not capture ' + theme)
        window.close()
        del engine
    return 0


if __name__ == '__main__':
    sys.exit(main())
