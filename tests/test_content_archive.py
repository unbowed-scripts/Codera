"""Parity, bounded memory, and isolated runtime checks for packaged courses."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from content_archive import LessonArchive, read_projects
from curriculum_source import LESSONS, TRACKS
from section_source import PROJECTS
from tools.pack_courses import pack_courses

ROOT = Path(__file__).resolve().parents[1]


class ContentArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'courses.zip'
        self.raw, self.packed = pack_courses(self.path)

    def test_all_content_survives_compression(self):
        catalog = LessonArchive(self.path)
        self.assertEqual(catalog.tracks, TRACKS)
        self.assertEqual(list(catalog), list(LESSONS))
        for key, lesson in LESSONS.items():
            self.assertEqual(catalog[key], lesson, key)
        self.assertEqual(read_projects(self.path), json.loads(json.dumps(PROJECTS)))
        self.assertLess(self.packed, self.raw * 0.6)
        with ZipFile(self.path) as archive:
            self.assertIsNone(archive.testzip())

    def test_index_does_not_decode_lessons_and_cache_is_bounded(self):
        catalog = LessonArchive(self.path, cache_size=2)
        self.assertEqual(len(catalog), len(LESSONS))
        self.assertIn('start/1', catalog)
        self.assertNotIn('missing', catalog)
        self.assertEqual(set(catalog.keys()), set(LESSONS))
        self.assertEqual(len(catalog._cache), 0)
        first = catalog['start/1']
        catalog['start/2']
        self.assertIs(catalog['start/1'], first)
        catalog['start/3']
        self.assertEqual(list(catalog._cache), ['start/1', 'start/3'])
        with self.assertRaises(KeyError):
            catalog['missing']
        for key in catalog:
            catalog[key]
            self.assertLessEqual(len(catalog._cache), 2)
        self.assertEqual([p.name for p in self.path.parent.iterdir()], ['courses.zip'])

    def test_reproducible_build(self):
        other = self.path.with_name('other.zip')
        pack_courses(other)
        self.assertEqual(other.read_bytes(), self.path.read_bytes())

    def test_runtime_without_authored_modules_and_progress_compatibility(self):
        for name in ('backend', 'curriculum', 'section_content', 'content_models',
                     'content_archive', 'language_catalog', 'themes', 'ai_tutor', 'practice_hints', 'credentials', 'workspace', 'runtime_manager', 'terminal_session', 'terminal_preferences'):
            shutil.copy2(ROOT / f'{name}.py', self.path.parent)
        script = '''
import sys
from pathlib import Path
from PySide6.QtCore import QSettings
from backend import Backend
from curriculum import LESSONS
from section_content import PROJECTS, questions
s = QSettings(str(Path('state.ini').resolve()), QSettings.IniFormat)
s.setValue('completed', ['start/1', 'missing'])
s.setValue('practiced', ['start/2'])
s.setValue('sectionTests', ['start'])
s.setValue('sectionProjects', ['start'])
b = Backend(s)
assert b.completed == {'start/1'} and b.practiced == {'start/2'}
assert b.section_tests == {'start'} and b.section_projects == {'start'}
assert not LESSONS._cache
for key in LESSONS:
    b.open('lesson', key)
    lesson = LESSONS[key]
    assert b.page['theory'] == lesson.theory
    for i, exercise in enumerate(lesson.exercises):
        b.answer(key, i, exercise.answer)
    b.check()
    b.markPractice(True)
for key in PROJECTS:
    b.open('checkpoint', key)
    for i, question in enumerate(questions(key)):
        b.answerTest(i, str(question['correct']) if question['options'] else question['answer'])
    b.checkTest()
    b.markProject(True)
r = Backend(s)
assert r.completed == set(LESSONS) and r.practiced == set(LESSONS)
assert r.section_tests == set(PROJECTS) and r.section_projects == set(PROJECTS)
s.sync()
assert Path('state.ini').stat().st_size < 8192
assert len(LESSONS._cache) <= 12
assert not {'core_content', 'web_content', 'web_extended_content', 'web_projects',
            'curriculum_source', 'section_source'} & sys.modules.keys()
print('Full progress bytes:', Path('state.ini').stat().st_size)
'''
        result = subprocess.run([sys.executable, '-c', script], cwd=self.path.parent,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
