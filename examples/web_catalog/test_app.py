import sqlite3
import tempfile
import unittest
from pathlib import Path
from examples.web_catalog.app import create_app


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'catalog.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.path})
        self.client = self.app.test_client()

    def test_filters_pages_and_boundaries(self):
        first = self.client.get('/api/books?limit=2').json
        second = self.client.get('/api/books?page=2&limit=2').json
        self.assertEqual(first['total'], 4)
        self.assertEqual([b['id'] for b in first['items']], [1, 2])
        self.assertEqual([b['id'] for b in second['items']], [3, 4])
        self.assertEqual(self.client.get('/api/books?q=Python&category=1').json['total'], 2)
        self.assertEqual(self.client.get('/api/books?q=Python&category=2').json['items'], [])
        self.assertEqual(self.client.get('/api/books?page=9').json['items'], [])
        for query in ['page=0', 'page=x', 'limit=0', 'limit=51', 'category=-1', 'q=' + 'a'*81]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get('/api/books?' + query).status_code, 400)
        self.assertEqual(self.client.get('/api/books/999').status_code, 404)

    def test_escape_sql_and_restart(self):
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT INTO books VALUES (5, ?, 1)', ("<script>alert('x')</script>",))
        html = self.client.get('/?q=%3Cscript%3E').get_data(as_text=True)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn("<script>alert", html)
        self.assertEqual(self.client.get('/api/books', query_string={'q': "' OR 1=1 --"}).json['items'], [])
        restored = create_app({'TESTING': True, 'DATABASE': self.path}).test_client()
        self.assertEqual(restored.get('/api/books/5').json['category'], 'Python')
        self.assertEqual(restored.get('/api/books').json['total'], 5)
        self.assertEqual(restored.post('/api/books', json={'title': 'Change'}).status_code, 405)
