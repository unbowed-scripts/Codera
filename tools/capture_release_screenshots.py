"""Capture release documentation at regular and narrow widths with isolated state."""
import os
from pathlib import Path
import sys
import tempfile
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QSettings, QMetaObject, QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from backend import Backend
from main import create_engine

app = QGuiApplication([])
with tempfile.TemporaryDirectory() as folder:
    backend = Backend(QSettings(folder + '/state.ini', QSettings.IniFormat))
    backend.reducedMotion = True
    engine = create_engine(backend)
    window = engine.rootObjects()[0]
    QMetaObject.invokeMethod(window, 'enterCourse')
    menu = window.findChild(QObject, 'settingsMenu')
    output = ROOT / 'docs/images'
    output.mkdir(exist_ok=True)
    for name, width, height in [('wide', 1380, 1000), ('narrow', 390, 780)]:
        window.setWidth(width)
        window.setHeight(height)
        QMetaObject.invokeMethod(menu, 'open')
        QTest.qWait(200)
        assert window.grabWindow().save(str(output / ('settings-' + name + '.png')))
        if name == 'narrow':
            def walk(item):
                yield item
                for child in item.childItems():
                    yield from walk(child)
            card = next(item for item in walk(window.contentItem()) if item.objectName() == 'themeCard_light')
            card.forceActiveFocus()
            QTest.qWait(100)
            assert window.grabWindow().save(str(output / 'settings-narrow-themes.png'))
        QMetaObject.invokeMethod(menu, 'close')
    window.setWidth(1100)
    window.setHeight(800)
    QMetaObject.invokeMethod(menu, 'open')
    info = window.findChild(QObject, 'releaseInfo')
    info.setProperty('about', True)
    QMetaObject.invokeMethod(info, 'open')
    QTest.qWait(200)
    assert window.grabWindow().save(str(output / 'about.png'))
    info.setProperty('about', False)
    QTest.qWait(150)
    assert window.grabWindow().save(str(output / 'updates.png'))
    window.close()
    del engine
