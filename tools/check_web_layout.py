"""Render Web lessons and capstones at desktop and phone widths using isolated progress."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QSettings, QMetaObject, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from backend import Backend
from curriculum import TRACKS, LESSONS
from main import create_engine


def walk(item):
    yield item
    for child in item.childItems():
        yield from walk(child)


def main():
    app = QGuiApplication.instance() or QGuiApplication([])
    output = ROOT / 'build/web-preview'
    output.mkdir(parents=True, exist_ok=True)
    messages = []
    old = qInstallMessageHandler(lambda kind, context, message: messages.append(message))
    with tempfile.TemporaryDirectory() as folder:
        backend = Backend(QSettings(str(Path(folder) / 'state.ini'), QSettings.IniFormat))
        backend.reducedMotion = True
        engine = create_engine(backend)
        window = engine.rootObjects()[0]
        window.setProperty('inCourse', True)
        def find(name):
            return next(i for i in walk(window.contentItem()) if i.objectName() == name)
        for width, height in ((1380, 940), (360, 800)):
            window.setWidth(width)
            window.setHeight(height)
            for section in TRACKS['Web']:
                for i in range(1, 7):
                    key = f'{section.id}/{i}'
                    backend.open('lesson', key)
                    QTest.qWait(60)
                    view = find('courseViewport')
                    view.setProperty('contentY', 0)
                    QTest.qWait(20)
                    assert view.property('contentWidth') <= view.width()
                    theory = find('lessonTheory')
                    assert theory.height() >= theory.property('contentHeight') - 1
                    for item in walk(window.contentItem()):
                        if item.isVisible() and item.property('truncated') is not None:
                            assert not item.property('truncated'), (width, key, item.property('text'))
                    if key in ('web-basics/6', 'web-app/1', 'web-data/5', 'web-quality/6', 'web-models/5', 'web-users/4', 'web-delivery/6'):
                        window.grabWindow().save(str(output / f'{width}-{key.replace("/", "-")}.png'))
                backend.completed.update(f'{section.id}/{i}' for i in range(1, 7))
                backend.section_tests.add(section.id)
                backend.open('checkpoint', section.id)
                QTest.qWait(80)
                QMetaObject.invokeMethod(find('projectHint'), 'clicked')
                QMetaObject.invokeMethod(find('projectHint'), 'clicked')
                QMetaObject.invokeMethod(find('showProjectExample'), 'clicked')
                QTest.qWait(60)
                view = find('courseViewport')
                hint = find('projectHint')
                view.setProperty('contentY', hint.mapToItem(view.property('contentItem'), 0, 0).y())
                QTest.qWait(30)
                window.grabWindow().save(str(output / f'{width}-{section.id}-hints.png'))
                for item in walk(window.contentItem()):
                    if item.isVisible() and item.property('truncated') is not None:
                        assert not item.property('truncated'), (width, section.id, item.property('text'))
            backend.open('overview', 'Web')
            QTest.qWait(60)
            find('courseViewport').setProperty('contentY', 0)
            QTest.qWait(30)
            window.grabWindow().save(str(output / f'{width}-overview.png'))
        window.close()
        engine.deleteLater()
        QTest.qWait(20)
    qInstallMessageHandler(old)
    assert not messages, '\n'.join(messages)
    print(f'{sum(len(s.levels) for s in TRACKS["Web"])} Web lessons and {len(TRACKS["Web"])} capstones checked at 1380 and 360 px:', output)


if __name__ == '__main__':
    main()
