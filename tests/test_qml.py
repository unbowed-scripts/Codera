import os
os.environ.setdefault('QT_QPA_PLATFORM', 'windows' if os.name == 'nt' else 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
import tempfile
import unittest
from PySide6.QtGui import QGuiApplication, QInputMethodEvent, QWheelEvent
from PySide6.QtCore import QObject, QSettings, QMetaObject, Q_ARG, Qt, QPoint, QPointF, qInstallMessageHandler
from PySide6.QtTest import QTest
from PySide6.QtQuick import QQuickItem
from backend import Backend
from curriculum import LESSONS, TRACKS
from main import create_engine

app = QGuiApplication.instance() or QGuiApplication([])


def walk(item):
    yield item
    for child in item.childItems():
        yield from walk(child)


class QuickTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.messages = []
        self.handler = qInstallMessageHandler(lambda kind, context, message: self.messages.append(message))
        self.backend = Backend(QSettings(self.temp.name + '/state.ini', QSettings.IniFormat))
        self.engine = create_engine(self.backend)
        self.assertTrue(self.engine.rootObjects(), self.messages)
        self.window = self.engine.rootObjects()[0]
        self.call('enterCourse')
        QTest.qWait(40)
        self.view = self.find('courseViewport')

    def tearDown(self):
        self.window.close()
        self.engine.deleteLater()
        app.sendPostedEvents(None, 0)
        QTest.qWait(20)
        qInstallMessageHandler(self.handler)
        self.temp.cleanup()
        self.assertEqual(self.messages, [], '\n'.join(self.messages))

    def find(self, name):
        return next(item for item in walk(self.window.contentItem()) if item.objectName() == name)

    def call(self, name, *args):
        return QMetaObject.invokeMethod(self.window, name, *[Q_ARG('QVariant', arg) for arg in args])

    def navigate(self, kind, key):
        self.call('navigate', kind, key)
        QTest.qWait(260)
        self.assertFalse(self.window.property('changing'))
        self.assertAlmostEqual(self.view.opacity(), 1)

    def test_real_click_navigation_and_no_duplicate_selection(self):
        target = self.find('continueLearning')
        pos = target.mapToScene(target.boundingRect().center()).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, pos)
        QTest.qWait(260)
        self.assertEqual(self.backend.routeKey, 'lesson:start/1')
        self.view.setProperty('contentY', 200)
        self.call('navigate', 'lesson', 'start/1'); QTest.qWait(240)
        self.assertEqual(self.view.property('contentY'), 200)
        self.assertEqual(self.window.property('commits'), 1)

    def test_rapid_clicks_latest_wins_and_scroll_restores(self):
        self.navigate('lesson', 'start/1')
        self.view.setProperty('contentY', 280)
        self.call('navigate', 'section', 'logic')
        self.call('navigate', 'lesson', 'start/2')
        self.call('navigate', 'lesson', 'start/3')
        QTest.qWait(280)
        self.assertEqual(self.backend.routeKey, 'lesson:start/3')
        self.assertFalse(self.window.property('changing'))
        self.navigate('lesson', 'start/1')
        self.assertAlmostEqual(self.view.property('contentY'), 280, delta=1)
        self.call('navigate', 'lesson', 'bogus'); QTest.qWait(40)
        self.assertFalse(self.window.property('changing'))
        self.assertEqual(self.backend.routeKey, 'lesson:start/1')

    def test_sidebar_scroll_is_preserved_within_track(self):
        sidebar = self.find('sidebar')
        sidebar.setProperty('expanded', {s.id: True for s in TRACKS['Python Core']})
        QTest.qWait(40)
        listing = self.find('topicList')
        listing.setProperty('contentY', 300)
        self.navigate('lesson', 'start/2')
        self.assertEqual(listing.property('contentY'), 300)
        self.navigate('lesson', 'start/3')
        self.assertEqual(listing.property('contentY'), 300)

    def test_title_does_not_move_during_reveal(self):
        self.call('navigate', 'lesson', 'start/1')
        samples = []
        for _ in range(24):
            QTest.qWait(12)
            if self.backend.routeKey == 'lesson:start/1' and self.view.opacity() > .05:
                title = self.find('pageTitle')
                samples.append(title.mapToScene(title.boundingRect().topLeft()).y())
        self.assertGreater(len(samples), 4)
        self.assertLessEqual(max(samples) - min(samples), .5)

    def test_checking_answers_keeps_scroll_and_geometry(self):
        self.navigate('lesson', 'start/1')
        self.view.setProperty('contentY', 350)
        first = self.find('answer0')
        last = self.find('answer1')
        before_y = last.mapToScene(last.boundingRect().topLeft()).y()
        before_height = self.view.property('contentHeight')
        self.backend.check(); QTest.qWait(40)
        self.assertEqual(self.view.property('contentY'), 350)
        self.assertAlmostEqual(self.view.property('contentHeight'), before_height, delta=.5)
        self.assertAlmostEqual(last.mapToScene(last.boundingRect().topLeft()).y(), before_y, delta=.5)
        for i, ex in enumerate(LESSONS['start/1'].exercises):
            field = self.find('answer'+str(i)); field.forceActiveFocus()
            event = QInputMethodEvent(); event.setCommitString(ex.answer)
            QGuiApplication.sendEvent(field, event)
        QTest.keyClick(self.window, Qt.Key_Return); QTest.qWait(40)
        self.assertTrue(self.backend.lessonCompleted)
        self.assertEqual(self.view.property('contentY'), 350)

    def test_compact_drawer_does_not_reflow_page(self):
        self.window.setWidth(600);self.window.setHeight(600);QTest.qWait(40)
        self.navigate('lesson', 'start/1')
        self.view.setProperty('contentY', 180)
        width, height = self.view.width(), self.view.property('contentHeight')
        self.window.setProperty('drawerOpen', True); QTest.qWait(80)
        self.assertEqual(self.view.width(), width)
        self.assertEqual(self.view.property('contentHeight'), height)
        self.assertEqual(self.view.property('contentY'), 180)
        self.window.setProperty('drawerOpen', False)
        self.assertEqual(self.view.property('contentY'), 180)

    def test_every_core_lesson_renders_with_practice(self):
        self.backend.reducedMotion = True
        self.window.setWidth(600)
        self.window.setHeight(700)
        for key in LESSONS:
            with self.subTest(key=key):
                self.call('navigate', 'lesson', key)
                QTest.qWait(35)
                self.assertEqual(self.backend.routeKey, 'lesson:' + key)
                self.assertTrue(self.find('practiceDone').isVisible())
                self.assertLessEqual(self.view.property('contentWidth'), self.view.width())
                for item in walk(self.window.contentItem()):
                    if item.property('text') and item.property('font') is not None:
                        if item.property('truncated') is not None:
                            self.assertFalse(item.property('truncated'), item.property('text'))

    def test_practice_checkbox_and_next_section(self):
        self.navigate('lesson', 'start/6')
        self.backend.completed.add('start/6')
        self.backend.progressChanged.emit()
        self.view.setProperty('contentY', self.view.property('contentHeight') - self.view.height())
        QTest.qWait(40)
        checkbox = self.find('practiceDone')
        pos = checkbox.mapToScene(checkbox.boundingRect().center()).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, pos)
        QTest.qWait(30)
        self.assertTrue(self.backend.practiceCompleted)
        target = self.find('nextLesson')
        pos = target.mapToScene(target.boundingRect().center()).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, Qt.NoModifier, pos)
        QTest.qWait(260)
        self.assertEqual(self.backend.routeKey, 'lesson:logic/1')
        self.assertFalse(self.backend.practiceCompleted)

    def test_themes_update_without_losing_answer_or_scroll(self):
        self.navigate('lesson', 'start/1')
        self.backend.answer('start/1', 0, 'Привет, Python!')
        self.view.setProperty('contentY', 200)
        for theme in self.backend.themeIds:
            self.backend.theme = theme
            QTest.qWait(40)
            self.assertEqual(self.window.color().name(), self.backend.colors['background'])
            self.assertEqual(self.view.property('contentY'), 200)
            self.assertEqual(self.backend.page['exercises'][0]['answer'], 'Привет, Python!')
            selector = self.find('trackSelector')
            QMetaObject.invokeMethod(selector.findChild(QObject, 'trackSelectorPopup'), 'open')
            QTest.qWait(40)
            popup = selector.findChild(QObject, 'trackSelectorPopup')
            self.assertTrue(popup.property('visible'))
            self.assertEqual(popup.property('background').property('color').name(), self.backend.colors['surface'])
            QMetaObject.invokeMethod(popup, 'close')
        self.window.setWidth(600)
        QTest.qWait(40)
        selector = self.find('themeSelector')
        right = selector.mapToScene(QPointF(selector.width(), 0)).x()
        self.assertLessEqual(right, self.window.width())
        # Keyboard changes the theme through the actual selector signal.
        selector.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Home)
        QTest.keyClick(self.window, Qt.Key_Down)
        QTest.qWait(40)
        self.assertEqual(self.backend.theme, 'blue')

    def test_wheel_is_immediate_bounded_and_keeps_touchpad_precision(self):
        self.navigate('lesson', 'start/1')
        self.view.setProperty('contentY', 0)
        pos = self.view.mapToScene(QPointF(self.view.width() / 2, self.view.height() / 2))
        def wheel(angle, pixels=0):
            event = QWheelEvent(pos, pos, QPoint(0, pixels), QPoint(0, angle),
                                Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
            QGuiApplication.sendEvent(self.window, event)
            QTest.qWait(20)
        wheel(-120)
        self.assertAlmostEqual(self.view.property('contentY'), 96, delta=1)
        wheel(0, -17)
        self.assertAlmostEqual(self.view.property('contentY'), 113, delta=1)
        QTest.qWait(180)
        self.assertAlmostEqual(self.view.property('contentY'), 113, delta=1)
        wheel(12000)
        self.assertEqual(self.view.property('contentY'), 0)
        wheel(-120000)
        self.assertAlmostEqual(self.view.property('contentY'), self.view.property('contentHeight') - self.view.height(), delta=1)

    def test_all_pages_resize_and_reduced_motion(self):
        self.backend.reducedMotion = True
        self.window.setWidth(600);self.window.setHeight(600)
        for track, sections in TRACKS.items():
            self.navigate('overview', track)
            for section in sections:
                self.navigate('section', section.id)
                self.navigate('lesson', section.id + '/1')
                self.assertLessEqual(self.view.property('contentWidth'), self.view.width())
        self.navigate('route', 'guide')
        self.call('leaveCourse');QTest.qWait(40)
        self.call('enterCourse');QTest.qWait(40)
        self.assertEqual(self.backend.routeKey, 'route:guide')


if __name__ == '__main__':
    unittest.main()
