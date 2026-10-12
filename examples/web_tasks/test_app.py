import sqlite3
import tempfile
import unittest
from pathlib import Path
from werkzeug.security import check_password_hash
from examples.web_tasks.app import create_app


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'tasks.sqlite3')
        self.config = {'TESTING': True, 'DATABASE': self.path, 'SECRET_KEY': 'only-a-test-secret-that-is-long-enough'}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.password = 'learning-only-password'

    def send(self, client, method, path, data=None):
        token = client.get('/api/csrf').json['csrf']
        return client.open(path, method=method, json=data or {}, headers={'X-CSRF-Token': token})

    def account(self, client, name):
        self.assertEqual(self.send(client, 'POST', '/auth/register', {'username': name, 'password': self.password}).status_code, 201)
        self.assertEqual(self.send(client, 'POST', '/auth/login', {'username': name, 'password': self.password}).status_code, 200)

    def test_registration_hash_login_logout_and_csrf(self):
        self.assertEqual(self.client.get('/api/tasks').status_code, 401)
        self.assertEqual(self.client.post('/auth/register', json={'username': 'anna', 'password': self.password}).status_code, 400)
        self.account(self.client, 'anna')
        duplicate = self.send(self.client, 'POST', '/auth/register', {'username': 'Anna', 'password': self.password})
        self.assertEqual(duplicate.status_code, 409)
        with sqlite3.connect(self.path) as db:
            hashed = db.execute('SELECT password_hash FROM users').fetchone()[0]
        self.assertNotEqual(hashed, self.password)
        self.assertTrue(check_password_hash(hashed, self.password))
        self.assertEqual(self.send(self.client, 'POST', '/auth/logout').status_code, 200)
        self.assertEqual(self.client.get('/api/tasks').status_code, 401)
        self.assertEqual(self.send(self.client, 'POST', '/auth/login', {'username': 'anna', 'password': 'incorrect-password'}).status_code, 401)
        self.assertEqual(self.client.get('/api/tasks').status_code, 401)
        token = self.client.get('/api/csrf').json['csrf']
        self.assertEqual(self.client.post('/auth/login', json={'username': 'anna', 'password': self.password}, headers={'X-CSRF-Token': token}).status_code, 200)
        self.assertEqual(self.client.post('/api/tasks', json={'title': 'Old token'}, headers={'X-CSRF-Token': token}).status_code, 400)
        self.assertEqual(self.client.get('/auth/logout').status_code, 405)

    def test_owner_crud_and_other_user_cannot_read_or_change(self):
        self.account(self.client, 'anna')
        created = self.send(self.client, 'POST', '/api/tasks', {'title': 'Original', 'owner_id': 999})
        self.assertEqual(created.status_code, 201)
        location = created.headers['Location']
        other = self.app.test_client()
        self.account(other, 'boris')
        self.assertEqual(other.get('/api/tasks').json['items'], [])
        self.assertEqual(other.get(location).status_code, 404)
        self.assertEqual(self.send(other, 'PATCH', location, {'title': 'Stolen'}).status_code, 404)
        self.assertEqual(self.send(other, 'DELETE', location).status_code, 404)
        task_id = created.json['id']
        self.assertEqual(self.send(other, 'POST', f'/tasks/{task_id}/toggle').status_code, 404)
        self.assertEqual(self.send(other, 'POST', f'/tasks/{task_id}/delete').status_code, 404)
        self.assertEqual(self.client.get(location).json['title'], 'Original')
        self.assertEqual(self.send(self.client, 'PATCH', location, {'title': 'Changed', 'done': True}).json['done'], 1)
        self.assertEqual(self.send(self.client, 'DELETE', location).status_code, 204)
        self.assertEqual(self.client.get(location).status_code, 404)

    def test_invalid_payloads_do_not_change_data(self):
        self.account(self.client, 'anna')
        created = self.send(self.client, 'POST', '/api/tasks', {'title': 'Keep'})
        location = created.headers['Location']
        for data in [{'title': ''}, {'title': 42}, {'title': 'x'*121}, {'title': 'Changed', 'done': 'false'}, {'owner_id': 2}]:
            with self.subTest(data=data):
                self.assertEqual(self.send(self.client, 'PATCH', location, data).status_code, 400)
                self.assertEqual(self.client.get(location).json['title'], 'Keep')
        self.assertEqual(self.client.patch(location, json={'title': 'No CSRF'}).status_code, 400)
        token = self.client.get('/api/csrf').json['csrf']
        self.assertEqual(self.client.post('/api/tasks', json=[], headers={'X-CSRF-Token': token}).status_code, 400)
        self.assertEqual(self.client.post('/api/tasks', data='x'*20000, content_type='application/json', headers={'X-CSRF-Token': token}).status_code, 413)
        self.assertEqual(len(self.client.get('/api/tasks').json['items']), 1)

    def test_html_forms_escaping_and_restart(self):
        token = self.client.get('/api/csrf').json['csrf']
        data = {'username': 'anna', 'password': self.password, 'csrf': token}
        self.assertEqual(self.client.post('/auth/register', data=data).status_code, 303)
        self.assertEqual(self.client.post('/auth/login', data=data).status_code, 303)
        token = self.client.get('/api/csrf').json['csrf']
        self.assertEqual(self.client.post('/tasks', data={'csrf': token, 'title': '<script>test</script>'}).status_code, 303)
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>test', html)
        task_id = self.client.get('/api/tasks').json['items'][0]['id']
        self.assertEqual(self.client.post(f'/tasks/{task_id}/toggle', data={'csrf': token}).status_code, 303)
        restored = create_app(self.config).test_client()
        self.assertEqual(self.send(restored, 'POST', '/auth/login', {'username': 'anna', 'password': self.password}).status_code, 200)
        self.assertEqual(restored.get('/api/tasks').json['items'][0]['done'], 1)
        self.assertEqual(self.client.post(f'/tasks/{task_id}/delete', data={'csrf': token}).status_code, 303)
        self.assertEqual(self.client.get('/api/tasks').json['items'], [])

    def test_production_requires_secret_and_sets_secure_cookie(self):
        with self.assertRaises(ValueError):
            create_app(dict(self.config, PRODUCTION=True, SECRET_KEY=''))
        app = create_app(dict(self.config, PRODUCTION=True))
        response = app.test_client().get('/api/csrf', base_url='https://localhost')
        self.assertIn('Secure;', response.headers['Set-Cookie'])
        self.assertIn('HttpOnly;', response.headers['Set-Cookie'])
        self.assertIn('SameSite=Lax', response.headers['Set-Cookie'])
        self.assertFalse(app.debug)
