import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from examples.habit_tracker.service import add_habit, mark_habit, delete_habit, validate_habits
from examples.habit_tracker.storage import load, save
from examples.habit_tracker.__main__ import main

ROOT = Path(__file__).resolve().parents[1]


class HabitTests(unittest.TestCase):
    def test_marks_are_idempotent_and_validate_before_mutation(self):
        habits = []
        habit = add_habit(habits, ' Python ')
        self.assertEqual(habit['name'], 'Python')
        self.assertTrue(mark_habit(habits, habit['id'], '2024-02-29'))
        self.assertFalse(mark_habit(habits, habit['id'], '2024-02-29'))
        for invalid in ['2023-02-29', 'no-date', '20240301', None]:
            with self.assertRaises(ValueError):
                mark_habit(habits, habit['id'], invalid)
        with self.assertRaises(ValueError):
            mark_habit(habits, 'missing', '2024-03-01')
        self.assertEqual(habit['days'], ['2024-02-29'])
        delete_habit(habits, habit['id'])
        self.assertEqual(habits, [])

    def test_invalid_records(self):
        invalid = [None, {}, [None], [{'id': 'a', 'name': ' ', 'days': []}],
                   [{'id': 'a', 'name': 'x', 'days': ['bad']}],
                   [{'id': 'a', 'name': 'x', 'days': ['2024-01-01'] * 2}],
                   [{'id': 'a', 'name': 'x', 'days': []}] * 2,
                   [{'id': 'a', 'name': 'x', 'days': [True]}]]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_habits(data)
        for name in ['', '  ', None, 7]:
            with self.assertRaises(ValueError):
                add_habit([], name)

    def test_roundtrip_and_failed_replace_preserves_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'data.json'
            self.assertEqual(load(path), [])
            habits = []
            add_habit(habits, 'Учить Python')
            save(path, habits)
            self.assertEqual(load(path), habits)
            old = path.read_bytes()
            add_habit(habits, 'Читать')
            with patch.object(Path, 'replace', side_effect=PermissionError('test')):
                with self.assertRaises(PermissionError):
                    save(path, habits)
            self.assertEqual(path.read_bytes(), old)
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_cli_rejects_corruption_without_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'data.json'
            for payload in ['{broken', '{}', '\ufffd']:
                path.write_text(payload, encoding='utf-8')
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['--file', str(path), 'add', 'Python']), 1)
                self.assertEqual(path.read_text(encoding='utf-8'), payload)

    def test_cli_survives_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'data.json'
            def run(*args):
                return subprocess.run([sys.executable, '-X', 'utf8', '-m', 'examples.habit_tracker',
                                       '--file', str(path), *args], cwd=ROOT,
                                      capture_output=True, encoding='utf-8', timeout=10)
            self.assertEqual(run('add', 'Python').returncode, 0)
            key = json.loads(path.read_text())[0]['id']
            self.assertEqual(run('mark', key, '--date', '2024-01-01').returncode, 0)
            self.assertIn('уже отмечен', run('mark', key, '--date', '2024-01-01').stdout)
            self.assertIn('1 дн.', run('list').stdout)
            self.assertEqual(run('delete', key).returncode, 0)
            self.assertIn('Пока нет', run('list').stdout)
