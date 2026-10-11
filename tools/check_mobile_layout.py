"""Render desktop/phone layouts with isolated progress; check navigation and text.

Run: .venv/bin/python tools/check_mobile_layout.py
Screenshots: build/mobile-preview/
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QSettings, QMetaObject, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from backend import Backend
from main import create_engine


def walk(item):
    yield item
    for child in item.childItems():
        yield from walk(child)


def main():
    app = QGuiApplication([])
    output = ROOT / 'build/mobile-preview'
    output.mkdir(parents=True, exist_ok=True)
    messages = []
    previous = qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    with tempfile.TemporaryDirectory() as folder:
        backend = Backend(QSettings(folder + '/state.ini', QSettings.IniFormat))
        backend.reducedMotion = True
        engine = create_engine(backend)
        window = engine.rootObjects()[0]
        for width, height in ((1380, 940), (360, 800), (320, 640)):
            window.setWidth(width)
            window.setHeight(height)
            for page, key in (('landing', ''), ('overview', 'Python Core'),
                              ('section', 'start'), ('lesson', 'start/6'),
                              ('checkpoint', 'start'), ('settings', '')):
                window.setProperty('inCourse', page != 'landing')
                if page not in ('landing', 'settings'):
                    backend.open(page, key)
                if page == 'settings':
                    button = next(i for i in walk(window.contentItem()) if i.objectName() == 'openSettings')
                    QMetaObject.invokeMethod(button, 'clicked')
                QTest.qWait(160)
                assert window.width() == width
                assert window.grabWindow().save(str(output / f'{width}-{page}.png'))
                for item in walk(window.contentItem()):
                    if item.isVisible() and item.property('text') and item.property('truncated') is not None:
                        assert not item.property('truncated'), (width, page, item.property('text'))
                if page == 'settings':
                    QMetaObject.invokeMethod(window, 'goBack')
            backend.open('lesson', 'start/1')
            window.setProperty('inCourse', True)
            QMetaObject.invokeMethod(window, 'goBack')
            QTest.qWait(100)
            assert backend.routeKey == 'section:start'
            QMetaObject.invokeMethod(window, 'goBack')
            QTest.qWait(100)
            assert backend.routeKey == 'overview:Python Core'
            QMetaObject.invokeMethod(window, 'goBack')
            assert not window.property('inCourse')
        window.close()
        del engine
    qInstallMessageHandler(previous)
    assert not messages, '\n'.join(messages)
    print('Desktop and phone layouts/navigation passed; screenshots:', output)


if __name__ == '__main__':
    main()
