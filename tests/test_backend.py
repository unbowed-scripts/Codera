import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
import tempfile
import unittest
from PySide6.QtCore import QSettings
from backend import Backend
from curriculum import TRACKS, LESSONS


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = QSettings(self.temp.name + '/state.ini', QSettings.IniFormat)
        self.backend = Backend(self.settings)

    def tearDown(self):
        self.temp.cleanup()

    def test_existing_progress_and_motion_migrate(self):
        self.settings.setValue('completed', ['start/1', 'start/2', 'not-real'])
        self.settings.setValue('reducedMotion', True)
        restored = Backend(self.settings)
        self.assertEqual(restored.completed, {'start/1', 'start/2'})
        self.assertTrue(restored.reducedMotion)
        self.assertEqual(restored.progress['nextKey'], 'start/3')

    def test_answers_drafts_completion_and_persistence(self):
        b = self.backend
        for key, lesson in LESSONS.items():
            b.open('lesson', key)
            b.check()
            self.assertNotIn(key, b.completed)
            for i, exercise in enumerate(lesson.exercises):
                b.answer(key, i, ' '+exercise.answer+' ')
            b.answer(key, 0, 'wrong'); b.check()
            self.assertFalse(b.feedback['passed'])
            b.answer(key, 0, lesson.exercises[0].answer); b.check()
            self.assertTrue(b.lessonCompleted)
            self.assertTrue(b.feedback['passed'])
        restored = Backend(self.settings)
        self.assertEqual(restored.completed, set(LESSONS))
        self.assertTrue(restored.progress['repeat'])
        b.open('overview', 'Web'); b.open('lesson', 'start/3')
        self.assertEqual(b.page['exercises'][0]['answer'], LESSONS['start/3'].exercises[0].answer)

    def test_all_routes_and_planned_lessons(self):
        b = self.backend
        keys = set()
        for track, sections in TRACKS.items():
            b.open('overview', track)
            for section in sections:
                self.assertTrue(5 <= len(section.levels) <= 10)
                b.open('section', section.id)
                for i in range(1, len(section.levels)+1):
                    key = f'{section.id}/{i}';keys.add(key)
                    self.assertTrue(b.validRoute('lesson', key))
                    b.open('lesson', key)
                    self.assertEqual(b.track, track)
                    if key not in LESSONS:
                        b.check(); self.assertNotIn(key, b.completed)
                        self.assertEqual(b.page['exercises'], [])
        self.assertEqual(len(keys), 74)
        route = b.routeKey
        self.assertFalse(b.open('lesson', 'bogus'))
        self.assertEqual(b.routeKey, route)

    def test_next_lesson_crosses_sections_and_stays_in_track(self):
        b = self.backend
        routes = [key for key, info in b.levels.items() if info[0] == 'Python Core']
        for index, key in enumerate(routes):
            b.open('lesson', key)
            self.assertEqual(b.nextLesson(), '')
            b.completed.add(key)
            expected = routes[index + 1] if index + 1 < len(routes) else ''
            self.assertEqual(b.nextLesson(), expected)

    def test_practice_is_separate_persistent_and_reversible(self):
        b = self.backend
        b.open('lesson', 'practice/6')
        b.markPractice(True)
        self.assertTrue(b.practiceCompleted)
        self.assertFalse(b.lessonCompleted)
        restored = Backend(self.settings)
        self.assertEqual(restored.practiced, {'practice/6'})
        self.assertFalse(restored.progress['webReady'])
        b.markPractice(False)
        self.assertFalse(b.practiceCompleted)
        b.completed = set(LESSONS)
        b.practiced = set(LESSONS)
        self.assertTrue(b.progress['webReady'])
        b.open('overview', 'Web')
        self.assertFalse(b.progress['webReady'])

    def test_repeated_route_and_scroll(self):
        b = self.backend
        count = []
        b.pageChanged.connect(lambda: count.append(1))
        b.open('lesson', 'start/1')
        b.saveScroll(b.routeKey, 444)
        self.assertFalse(b.open('lesson', 'start/1'))
        self.assertEqual(len(count), 1)
        b.open('section', 'start'); b.open('lesson', 'start/1')
        self.assertEqual(b.restoredScroll(), 444)


if __name__ == '__main__':
    unittest.main()
