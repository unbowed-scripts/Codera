import ast
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PySide6.QtCore import QSettings
from backend import Backend
from curriculum import LESSONS, TRACKS
from section_content import PROJECTS, questions
from web_content import WEB_CONTENT
from examples.web_catalog.test_app import CatalogTests
from examples.web_tasks.test_app import TaskTests
from examples.web_notes.test_app import NotesTests  # Include the runnable project's real tests.


class TheoryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs): self.tags.append(tag)


class WebCourseTests(unittest.TestCase):
    def test_all_sections_and_track_progress_are_independent(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = QSettings(str(Path(folder) / 'progress.ini'), QSettings.IniFormat)
            b = Backend(settings)
            core_keys = {key for key in LESSONS if not key.startswith('web-')}
            b.completed = core_keys.copy()
            b.practiced = core_keys.copy()
            b.section_tests = {s.id for s in TRACKS['Python Core']}
            b.section_projects = b.section_tests.copy()
            self.assertTrue(b.progress['webReady'])
            b.open('overview', 'Web')
            self.assertEqual(b.progress['ready'], 42)
            self.assertEqual(b.progress['done'], 0)
            self.assertEqual(b.progress['checkpointTotal'], 7)
            for section in TRACKS['Web']:
                b.open('checkpoint', section.id)
                self.assertFalse(b.assessment['unlocked'])
                for i in range(1, 7):
                    key = f'{section.id}/{i}'
                    b.open('lesson', key)
                    for n, exercise in enumerate(LESSONS[key].exercises):
                        b.answer(key, n, exercise.answer)
                    b.check()
                    b.markPractice(True)
                self.assertTrue(b.page['isSectionFinal'])
                b.open('checkpoint', section.id)
                self.assertTrue(b.assessment['unlocked'])
                for i, question in enumerate(questions(section.id)):
                    b.answerTest(i, str(question['correct']) if question['options'] else question['answer'])
                b.checkTest()
                self.assertTrue(b.assessment['testPassed'])
                b.markProject(True)
                self.assertTrue(b.assessment['projectDone'])
                self.assertIn('criteria', b.tutor_context('project'))
            self.assertEqual(b.nextSection(), '')
            self.assertTrue(b.page['isTrackFinal'])
            self.assertEqual(b.progress['done'], 42)
            restored = Backend(settings)
            self.assertTrue(restored.open('overview', 'Web'))
            self.assertEqual(restored.progress['sectionProjects'], 7)
            self.assertEqual(restored.progress['readyDone'], 42)

    def test_existing_web_progress_continues_into_new_sections(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = QSettings(str(Path(folder) / 'state.ini'), QSettings.IniFormat)
            old_sections = ('web-basics', 'web-app', 'web-data', 'web-quality')
            keys = [f'{section}/{i}' for section in old_sections for i in range(1, 7)]
            settings.setValue('completed', keys)
            settings.setValue('practiced', keys)
            settings.setValue('sectionTests', list(old_sections))
            settings.setValue('sectionProjects', list(old_sections))
            b = Backend(settings)
            b.open('overview', 'Web')
            self.assertEqual(b.progress['done'], 24)
            self.assertFalse(b.progress['repeat'])
            self.assertEqual(b.progress['nextKey'], 'web-models/1')
            b.open('checkpoint', 'web-quality')
            self.assertTrue(b.assessment['projectDone'])
            self.assertFalse(b.page['isTrackFinal'])
            self.assertEqual(b.nextSection(), 'web-models')
            b.open('checkpoint', 'web-delivery')
            self.assertTrue(b.page['isTrackFinal'])

    def test_theory_markup_and_complete_projects(self):
        for key, record in WEB_CONTENT.items():
            parser = TheoryParser()
            parser.feed(record[0])
            self.assertGreaterEqual(parser.tags.count('p'), 3, key)
            self.assertEqual(parser.tags.count('b'), 1, key)
            self.assertTrue(set(parser.tags) <= {'p', 'b', 'code', 'ul', 'li'}, key)
            self.assertTrue(record[4].startswith('1. '), key)
            self.assertTrue(record[5].startswith('• '), key)
        for section in TRACKS['Web']:
            project = PROJECTS[section.id]
            self.assertEqual(len(questions(section.id)), 8)
            self.assertEqual(len(project['hints']), len(project['hintCodes']))
            ast.parse(project['code'])
            for code in project['hintCodes']:
                ast.parse(code)
            # Run non-server capstones; the final server has end-to-end tests above.
            if section.id not in {'web-quality', 'web-models', 'web-users', 'web-delivery'}:
                with tempfile.TemporaryDirectory() as folder:
                    script = Path(folder) / 'project.py'
                    script.write_text(project['code'], encoding='utf-8')
                    result = subprocess.run([sys.executable, str(script)], cwd=folder, capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr.decode())
