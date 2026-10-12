import json
import os
import tempfile
from pathlib import Path
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from backend import Backend
from ai_tutor import endpoint_url

app = QGuiApplication.instance() or QGuiApplication([])


class TutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests = []
        cls.response = (200, {'choices': [{'message': {'content': 'Подсказка\n```python\nprint(42)\n```'}}]})
        cls.delay = 0
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                cls.requests.append((self.path, self.headers.get('Authorization'), json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                status, payload = cls.response
                time.sleep(cls.delay)
                self.send_response(status)
                self.end_headers()
                try: self.wfile.write(json.dumps(payload).encode())
                except (BrokenPipeError, ConnectionResetError): pass
            def log_message(self, *args): pass
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/v1'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.b = Backend(QSettings(self.temp.name + '/state.ini', QSettings.IniFormat))
        self.ai = self.b.tutor
        type(self).delay = 0
        type(self).response = (200, {'choices': [{'message': {'content': 'Подсказка\n```python\nprint(42)\n```'}}]})

    def tearDown(self):
        self.ai.disconnectModel()
        self.b.deleteLater()
        QTest.qWait(20)
        self.temp.cleanup()

    def wait(self):
        for _ in range(200):
            if not self.ai.busy: return
            QTest.qWait(10)
        self.fail('Request did not finish')

    def connect(self):
        self.ai.connectModel(self.url, 'test-model', 'test-secret')
        self.wait()
        self.assertTrue(self.ai.connected, self.ai.status)

    def test_context_and_credentials(self):
        self.connect()
        self.b.open('lesson', 'start/1')
        self.b.answer('start/1', 0, 'мой ответ')
        self.ai.ask('exercise:0', 'print(7)', 'Почему?')
        self.wait()
        path, auth, body = self.requests[-1]
        self.assertEqual(path, '/v1/chat/completions')
        self.assertEqual(auth, 'Bearer test-secret')
        context = json.loads(body['messages'][1]['content'])
        self.assertEqual(context['question_number'], 1)
        self.assertEqual(context['student_answer'], 'мой ответ')
        self.assertEqual(context['student_code'], 'print(7)')
        self.assertNotIn('test-secret', json.dumps(body))
        self.assertIn('```python', self.ai.state('exercise:0')['text'])
        self.assertNotIn('test-secret', Path(self.b.settings.fileName()).read_text())
        restored = Backend(self.b.settings)
        self.assertFalse(restored.tutor.connected)
        self.assertEqual(restored.tutor._key, '')
        self.b.open('lesson', 'logic/1')
        self.assertEqual(self.ai.state('exercise:0')['text'], '')
        self.assertIn('criteria', self.b.tutor_context('practice'))
        self.b.open('checkpoint', 'start')
        self.assertIsNone(self.b.tutor_context('test:0'))
        self.b.completed.update(f'start/{i}' for i in range(1, 7))
        self.assertEqual(self.b.tutor_context('test:0')['question_number'], 1)
        self.assertIsNone(self.b.tutor_context('project'))
        self.b.section_tests.add('start')
        self.assertIn('criteria', self.b.tutor_context('project'))

    def test_failures_retry_and_cancel_on_navigation(self):
        self.connect()
        self.b.open('lesson', 'start/1')
        for response in [(401, {}), (429, {}), (200, {}), (302, {})]:
            type(self).response = response
            self.ai.ask('practice', '', '')
            self.wait()
            self.assertTrue(self.ai.state('practice')['error'])
            self.assertFalse(self.ai.busy)
        type(self).response = (200, {'choices': [{'message': {'content': 'OK'}}]})
        self.ai.ask('practice', '', '')
        self.wait()
        self.assertEqual(self.ai.state('practice')['text'], 'OK')
        type(self).delay = .15
        self.ai.ask('practice', '', '')
        self.b.open('lesson', 'start/2')
        QTest.qWait(250)
        self.assertFalse(self.ai.busy)
        self.assertEqual(self.ai.state('practice')['text'], '')

    def test_project_hint_examples_compile(self):
        from practice_hints import PROJECT_HINT_CODES
        from section_content import PROJECTS
        self.assertEqual(PROJECT_HINT_CODES.keys(), {k for k in PROJECTS if not k.startswith('web-')})
        for key, snippets in PROJECT_HINT_CODES.items():
            self.assertEqual(len(snippets), len(PROJECTS[key]['hints']))
            for snippet in snippets:
                compile(snippet, '<hint:' + key + '>', 'exec')

    def test_url_validation(self):
        for bad in ('http://example.com/v1', 'https://user:secret@example.com', 'file:///tmp/api', 'https://example.com?key=secret'):
            with self.assertRaises(ValueError): endpoint_url(bad)
        self.assertEqual(endpoint_url('https://example.com/v1/').toString(), 'https://example.com/v1/chat/completions')
        self.assertEqual(endpoint_url(self.url + '/chat/completions').path(), '/v1/chat/completions')
