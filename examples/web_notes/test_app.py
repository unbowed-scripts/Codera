"""Run with python -m unittest discover -s examples/web_notes -p 'test_*.py'."""
import tempfile
import unittest
from pathlib import Path

try:
    from .app import create_app
except ImportError:
    from app import create_app


class NotesTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.config = {'TESTING': True, 'SECRET_KEY': 'only-for-isolated-tests',
                       'DATABASE': str(Path(self.folder.name) / 'test.sqlite3')}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.token = self.client.get('/api/csrf').json['csrf']
        self.headers = {'X-CSRF-Token': self.token}

    def tearDown(self):
        self.folder.cleanup()

    def create(self, title='Учить Web'):
        return self.client.post('/api/notes', json={'title': title}, headers=self.headers)

    def test_crud_and_persistence(self):
        response = self.create()
        self.assertEqual(response.status_code, 201)
        path = response.headers['Location']
        self.assertEqual(self.client.get(path).json['title'], 'Учить Web')
        self.assertEqual(create_app(self.config).test_client().get(path).json['title'], 'Учить Web')
        changed = self.client.patch(path, json={'title': '  Новый заголовок  '}, headers=self.headers)
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json['title'], 'Новый заголовок')
        deleted = self.client.delete(path, headers=self.headers)
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(deleted.data, b'')
        self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 404)

    def test_validation_and_missing_ids_do_not_change_data(self):
        for payload in [None, [], 42, {}, {'title': 42}, {'title': ''}, {'title': '   '}, {'title': 'x' * 81}]:
            response = self.client.post('/api/notes', data=__import__('json').dumps(payload),
                                        content_type='application/json', headers=self.headers)
            self.assertEqual(response.status_code, 400, payload)
        self.assertEqual(self.client.post('/api/notes', data='{broken', content_type='application/json', headers=self.headers).status_code, 400)
        self.assertEqual(self.client.post('/api/notes', data='text', headers=self.headers).status_code, 415)
        self.assertEqual(self.client.get('/api/notes').json, {'notes': []})
        self.assertEqual(self.create('x' * 80).status_code, 201)
        self.assertEqual(self.client.patch('/api/notes/999', json={'title': 'Test'}, headers=self.headers).status_code, 404)
        self.assertEqual(len(self.client.get('/api/notes').json['notes']), 1)

    def test_csrf_and_get_cannot_modify_notes(self):
        self.create()
        for headers in ({}, {'X-CSRF-Token': 'bad'}, {'X-CSRF-Token': 'неверно'}):
            self.assertEqual(self.client.post('/api/notes', json={'title': 'Other'}, headers=headers).status_code, 400)
            self.assertEqual(self.client.patch('/api/notes/1', json={'title': 'Other'}, headers=headers).status_code, 400)
            self.assertEqual(self.client.delete('/api/notes/1', headers=headers).status_code, 400)
        other = self.app.test_client()
        self.assertEqual(other.delete('/api/notes/1', headers=self.headers).status_code, 400)
        self.assertEqual(self.client.get('/notes/1/delete').status_code, 405)
        self.assertEqual(self.client.get('/api/notes/1').json['title'], 'Учить Web')

    def test_html_forms_escaping_search_and_sql_quotes(self):
        title = '<script>alert("test")</script> Python\'s 100%'
        response = self.client.post('/notes', data={'csrf': self.token, 'title': title})
        self.assertEqual(response.status_code, 303)
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)
        self.assertEqual(len(self.client.get('/api/notes', query_string={'q': 'PYTHON'}).json['notes']), 1)
        self.assertEqual(len(self.client.get('/api/notes', query_string={'q': '%'}).json['notes']), 1)
        self.assertEqual(self.client.get('/api/notes?q=missing').json['notes'], [])
        self.assertEqual(self.client.post('/notes/1/edit', data={'csrf': self.token, 'title': 'Changed'}).status_code, 303)
        self.assertEqual(self.client.get('/api/notes/1').json['title'], 'Changed')
        self.assertEqual(self.client.post('/notes/1/delete', data={'csrf': self.token}).status_code, 303)
        self.assertEqual(self.client.get('/api/notes').json['notes'], [])

    def test_oversize_payload(self):
        response = self.client.post('/api/notes', json={'title': 'x' * 20000}, headers=self.headers)
        self.assertEqual(response.status_code, 413)
        self.assertIn('error', response.json)
        self.assertEqual(self.client.get('/api/notes').json['notes'], [])


if __name__ == '__main__':
    unittest.main()
