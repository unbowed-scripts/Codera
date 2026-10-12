"""Read-only learning catalog: relations, filtering and stable pagination."""
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from flask import Flask, abort, render_template_string, request

PAGE = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Каталог книг</title><h1>Каталог книг</h1>
<form><label>Поиск <input name="q" value="{{ q }}" maxlength="80"></label>
<label>Категория <select name="category"><option value="">Все</option>
{% for c in categories %}<option value="{{ c.id }}" {% if category == c.id|string %}selected{% endif %}>{{ c.name }}</option>{% endfor %}
</select></label><button>Найти</button></form>
<p>Найдено: {{ total }}. Страница {{ page }}.</p>
<ul>{% for b in items %}<li>{{ b.title }} — {{ b.category }}</li>
{% else %}<li>Ничего не найдено.</li>{% endfor %}</ul>
{% if page > 1 %}<a href="{{ url_for('index', q=q, category=category, page=page-1, limit=limit) }}">Назад</a>{% endif %}
{% if page * limit < total %}<a href="{{ url_for('index', q=q, category=category, page=page+1, limit=limit) }}">Дальше</a>{% endif %}
</html>'''


def page_number(value, name, maximum):
    try:
        result = int(value)
    except (ValueError, TypeError):
        abort(400, description=f'{name}: нужно целое число')
    if not 1 <= result <= maximum:
        abort(400, description=f'{name}: число от 1 до {maximum}')
    return result


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(DATABASE=os.environ.get('CATALOG_DB', str(Path(__file__).with_name('catalog.sqlite3'))))
    app.config.update(config or {})

    def connect():
        db = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        return db

    with closing(connect()) as db, db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY, title TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id));
            CREATE INDEX IF NOT EXISTS books_category ON books(category_id);
        ''')
        db.executemany('INSERT OR IGNORE INTO categories VALUES (?, ?)', [(1, 'Python'), (2, 'Web')])
        db.executemany('INSERT OR IGNORE INTO books VALUES (?, ?, ?)', [
            (1, 'Функции Python', 1), (2, 'Тесты Python', 1),
            (3, 'HTTP и Flask', 2), (4, 'SQL для начинающих', 2)])

    def selection():
        q = request.args.get('q', '').strip()
        if len(q) > 80:
            abort(400, description='Поиск: не более 80 символов')
        category = request.args.get('category', '')
        page = page_number(request.args.get('page', '1'), 'page', 10000)
        limit = page_number(request.args.get('limit', '2'), 'limit', 50)
        conditions, params = [], []
        if q:
            # instr searches literal text; '%' and '_' are not wildcard operators here.
            conditions.append('instr(b.title, ?) > 0')
            params.append(q)
        if category:
            conditions.append('b.category_id = ?')
            params.append(page_number(category, 'category', 2147483647))
        where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
        with closing(connect()) as db:
            total = db.execute('SELECT count(*) FROM books b' + where, params).fetchone()[0]
            rows = db.execute('SELECT b.id, b.title, c.name AS category FROM books b '
                              'JOIN categories c ON c.id = b.category_id' + where +
                              ' ORDER BY b.id LIMIT ? OFFSET ?', params + [limit, (page - 1) * limit]).fetchall()
            categories = [dict(row) for row in db.execute('SELECT * FROM categories ORDER BY id')]
        return dict(items=[dict(row) for row in rows], total=total, page=page,
                    limit=limit, q=q, category=category, categories=categories)

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.get('/')
    def index():
        return render_template_string(PAGE, **selection())

    @app.get('/api/books')
    def books():
        data = selection()
        return {key: data[key] for key in ('items', 'total', 'page', 'limit')}

    @app.get('/api/books/<int:book_id>')
    def detail(book_id):
        with closing(connect()) as db:
            row = db.execute('SELECT b.id, b.title, c.name AS category FROM books b '
                             'JOIN categories c ON c.id = b.category_id WHERE b.id = ?', (book_id,)).fetchone()
        if row is None:
            abort(404, description='Книга не найдена')
        return dict(row)

    @app.errorhandler(400)
    @app.errorhandler(404)
    def error(error):
        return {'error': error.description}, error.code

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', debug=False)
