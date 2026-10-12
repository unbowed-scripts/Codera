"""Small capstone UI smoke: actual buttons, inputs, persistence and two widths."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
import tempfile
import unittest
from pathlib import Path
from PySide6.QtCore import QSettings, QMetaObject, Qt, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from backend import Backend
from curriculum import LESSONS
from section_content import PROJECTS, questions
from main import create_engine

app = QGuiApplication.instance() or QGuiApplication([])


def walk(item):
    yield item
    for child in item.childItems():
        yield from walk(child)


class CheckpointSmoke(unittest.TestCase):
    def test_section_flow(self):
        with tempfile.TemporaryDirectory() as folder:
            messages = []
            old = qInstallMessageHandler(lambda kind, context, text: messages.append(text))
            backend = Backend(QSettings(folder + '/state.ini', QSettings.IniFormat))
            backend.reducedMotion = True
            engine = create_engine(backend)
            self.assertTrue(engine.rootObjects(), messages)
            window = engine.rootObjects()[0]
            QMetaObject.invokeMethod(window, 'enterCourse')
            QTest.qWait(30)

            def find(name):
                return next(item for item in walk(window.contentItem()) if item.objectName() == name)

            def click(name):
                QTest.qWait(20)  # Let answer feedback and nested columns finish layout.
                item = find(name)
                view = find('courseViewport')
                top = item.mapToItem(view.property('contentItem'), 0, 0).y()
                view.setProperty('contentY', max(0, min(top - 40, view.property('contentHeight') - view.height())))
                QTest.qWait(20)
                self.assertTrue(item.isVisible(), name)
                self.assertTrue(item.isEnabled(), name)
                QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                                 item.mapToScene(item.boundingRect().center()).toPoint())
                QTest.qWait(40)

            try:
                # Each section has six recall questions, two interpretations and runnable code.
                for section, project in PROJECTS.items():
                    compile(project['code'], section + '.py', 'exec')
                    self.assertEqual(len(questions(section)), 8)
                    backend.open('checkpoint', section)
                    QTest.qWait(20)
                    self.assertFalse(backend.assessment['unlocked'])
                    self.assertTrue(find('checkpointStatus').isVisible())
                    backend.checkTest()
                    self.assertNotIn(section, backend.section_tests)

                for level in range(1, 7):
                    key = f'start/{level}'
                    backend.open('lesson', key)
                    for i, exercise in enumerate(LESSONS[key].exercises):
                        backend.answer(key, i, exercise.answer)
                    backend.check()
                QTest.qWait(30)
                click('lessonPracticeHint')
                click('nextLesson')
                self.assertEqual(backend.routeKey, 'checkpoint:start')
                self.assertTrue(backend.assessment['unlocked'])
                click('checkSectionTest')
                self.assertIn('0 / 8', backend.assessment['message'])
                for i, question in enumerate(questions('start')[:6]):
                    field = find('testAnswer' + str(i))
                    field.forceActiveFocus()
                    event = QInputMethodEvent()
                    event.setCommitString(question['answer'])
                    QGuiApplication.sendEvent(field, event)
                for i, question in enumerate(questions('start')[6:], 6):
                    click(f'testOption{i}_{question["correct"]}')
                click('checkSectionTest')
                self.assertTrue(backend.assessment['testPassed'])
                click('projectHint')
                click('projectHint')
                click('showProjectExample')
                self.assertTrue(find('projectCode').isVisible())
                click('copyProject')
                self.assertEqual(app.clipboard().text(), PROJECTS['start']['code'])
                # A compact visual check without a full regression run.
                output = Path(os.environ.get('PYTHONTECH_SMOKE_OUTPUT', folder))
                output.mkdir(parents=True, exist_ok=True)
                for width in (1380, 360):
                    window.setWidth(width)
                    window.setHeight(940 if width == 1380 else 700)
                    QTest.qWait(40)
                    view = find('courseViewport')
                    self.assertLessEqual(view.property('contentWidth'), view.width())
                    for item in walk(window.contentItem()):
                        if item.isVisible() and item.property('truncated') is not None:
                            self.assertFalse(item.property('truncated'), item.property('text'))
                    hint = find('projectHint')
                    view.setProperty('contentY', hint.mapToItem(view.property('contentItem'), 0, 0).y())
                    QTest.qWait(30)
                    window.grabWindow().save(str(output / f'project-hints-{width}.png'))
                    example = find('showProjectExample')
                    view.setProperty('contentY', example.mapToItem(view.property('contentItem'), 0, 0).y())
                    QTest.qWait(30)
                    window.grabWindow().save(str(output / f'checkpoint-{width}.png'))
                click('sectionProjectDone')
                self.assertTrue(backend.assessment['projectDone'])
                restored = Backend(backend.settings)
                self.assertIn('start', restored.section_tests)
                self.assertIn('start', restored.section_projects)
                click('nextSection')
                self.assertEqual(backend.routeKey, 'section:logic')
            finally:
                window.close()
                engine.deleteLater()
                app.sendPostedEvents(None, 0)
                QTest.qWait(20)
                qInstallMessageHandler(old)
            self.assertEqual(messages, [])


if __name__ == '__main__':
    unittest.main()
