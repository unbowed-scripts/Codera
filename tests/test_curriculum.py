"""Execute authored examples in isolated processes, never learner submissions."""
import ast
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from curriculum import TRACKS, LESSONS, check_answer
from web_content import WEB_EXPECTED

EXPECTED = {
    'start/1': 'Привет, Python!', 'start/2': 'Счёт: 5\n2 + 3', 'start/3': '5',
    'start/4': '2 5', 'start/5': 'Мира, через год тебе 21',
    'start/6': 'Мира, за 7 таких дней: 210 мин.',
    'logic/1': 'True\nFalse', 'logic/2': 'Хватает', 'logic/3': 'Хорошо',
    'logic/4': '3\n2\n1\nСтарт', 'logic/5': '10', 'logic/6': 'Угадал',
    'collections/1': 'Мира Аня\n3', 'collections/2': '1 читать\n2 писать\nписать',
    'collections/3': 'python-core\npython', 'collections/4': '7\n2\nTrue',
    'collections/5': 'Не указан\nname Мира\npoints 5',
    'collections/6': 'чай 2\nхлеб 1\nВсего: 3',
    'functions/1': 'Привет, Мира!\nПривет, Лев!', 'functions/2': '150\n20',
    'functions/3': '11\n10', 'functions/4': '[2, 4, 6, 8]\n[2, 4]',
    'functions/5': '24', 'functions/6': '1500.0\n32.0',
    'reliable/1': '9\nTrue', 'reliable/2': 'Учусь Python',
    'reliable/3': 'Нужно целое число', 'reliable/4': '1 0',
    'reliable/5': '', 'reliable/6': '0',
    'idioms/1': '3 2\nTrue\nTrue', 'idioms/2': '[16, 4]\nЛев',
    'idioms/3': "['a']\n['b']\nМира: True", 'idioms/4': '3\n[2, 1]\n[]',
    'idioms/5': 'Вызов\n5', 'idioms/6': 'Начало\nработа\nКонец',
    'objects/1': '20', 'objects/2': "['Python']", 'objects/3': '2\nКорзина: 2',
    'objects/4': '0', 'objects/5': 'Нужно положительное целое', 'objects/6': '5000',
    'tooling/1': None, 'tooling/2': 'Приложение запущено', 'tooling/3': 'Мира',
    'tooling/4': '2024-02-29\n2\n0.3\nUTC', 'tooling/5': '', 'tooling/6': '',
    'practice/1': '4\n0', 'practice/2': '75.0', 'practice/3': '4.0',
    'practice/4': 'X', 'practice/5': '5.00', 'practice/6': 'True\nFalse\n1',
}
EXPECTED.update(WEB_EXPECTED)
INPUTS = {'start/5': ['Мира', '20'], 'start/6': ['Мира', '30'], 'logic/6': ['7']}


class CurriculumTests(unittest.TestCase):
    def test_complete_core_and_unique_routes(self):
        routes = [f'{s.id}/{i}' for s in TRACKS['Python Core']
                  for i in range(1, len(s.levels) + 1)]
        self.assertEqual(len(routes), 54)
        self.assertEqual(len(routes), len(set(routes)))
        web_routes = [f'{s.id}/{i}' for s in TRACKS['Web'] for i in range(1, len(s.levels) + 1)]
        self.assertEqual(len(web_routes), 24)
        self.assertEqual(set(routes + web_routes), set(LESSONS))
        self.assertEqual(set(EXPECTED), set(LESSONS))
        for key, lesson in LESSONS.items():
            with self.subTest(key=key):
                for field in ['theory', 'code', 'explanation', 'remember', 'practice', 'criteria']:
                    self.assertTrue(getattr(lesson, field).strip(), field)
                self.assertGreaterEqual(len(lesson.exercises), 2)
                ast.parse(lesson.code)
                for exercise in lesson.exercises:
                    self.assertNotIn('\n', exercise.answer)
                    self.assertTrue(exercise.hint and exercise.explanation)
                    self.assertTrue(check_answer(exercise, ' ' + exercise.answer + ' '))
                    self.assertFalse(check_answer(exercise, ''))

    def test_all_examples_run_and_match_the_walkthrough(self):
        for key, lesson in LESSONS.items():
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                prefix = ('import builtins\n'
                          f'_answers = iter({INPUTS.get(key, [])!r})\n'
                          'builtins.input = lambda prompt="": next(_answers)\n')
                script = Path(folder) / 'example.py'
                script.write_text(prefix + lesson.code, encoding='utf-8')
                result = subprocess.run([sys.executable, '-X', 'utf8', str(script)], cwd=folder,
                                        capture_output=True, encoding='utf-8', timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                if EXPECTED[key] is not None:
                    self.assertEqual(result.stdout.strip(), EXPECTED[key])
                else:
                    self.assertEqual(result.stdout.splitlines()[0], '3')
                if key in {'reliable/5', 'tooling/5'}:
                    self.assertIn('Ran 1 test', result.stderr)
                    self.assertIn('OK', result.stderr)

    def test_game_loss_and_direction_hints(self):
        code = LESSONS['logic/6'].code
        prefix = 'answers = iter(["1", "9", "2"])\ninput = lambda prompt="": next(answers)\n'
        result = subprocess.run([sys.executable, '-X', 'utf8', '-c', prefix + code],
                                capture_output=True, encoding='utf-8', timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), 'Больше\nМеньше\nБольше\nПопытки закончились')
