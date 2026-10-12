"""Local single-user notes: Flask, SQLite, HTML forms and JSON API.
Run: python -m flask --app examples.web_notes.app run
This teaching app has no login; keep it on localhost.
"""
import os
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, abort, redirect, render_template_string, request, session, url_for

PAGE = '''<!doctype html>
<html lang="ru">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Мои заметки</title>
<style>
body { font: 1rem/1.6 system-ui; max-width: 48rem; margin: auto; padding: 1rem; }
input, button { font: inherit; padding: .5rem; max-width: 100%; box-sizing: border-box; }
form { margin-bottom: 1rem; } li { margin-bottom: 1.5rem; overflow-wrap: anywhere; }
label { display: block; } input[type=text] { width: 100%; }
</style>
<h1>Мои заметки</h1>
<form method="get"><label>Поиск <input type="text" name="q" value="{{ query }}"></label><button>Найти</button></form>
<form method="post" action="{{ url_for('create_form') }}">
<input type="hidden" name="csrf" value="{{ token }}">
<label>Новая заметка <input type="text" name="title" required maxlength="80"></label>
<button>Добавить</button></form>
<ul>{% for note in notes %}<li>
<form method="post" action="{{ url_for('edit_form', note_id=note['id']) }}">
<input type="hidden" name="csrf" value="{{ token }}">
<label>Заметка {{ note['id'] }} <input type="text" name="title" value="{{ note['title'] }}" required maxlength="80"></label>
<button>Сохранить</button></form>
<form method="post" action="{{ url_for('delete_form', note_id=note['id']) }}">
<input type="hidden" name="csrf" value="{{ token }}"><button>Удалить</button></form>
</li>{% else %}<li>Заметок пока нет или поиск ничего не нашёл.</li>{% endfor %}</ul>
<p>Учебный локальный блокнот. Данные сохраняются в SQLite.</p>
</html>'''


def clean_title(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 80:
        raise ValueError('Заголовок должен содержать от 1 до 80 символов.')
    return value.strip()


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('NOTES_SECRET') or secrets.token_hex(32),
        DATABASE=os.environ.get('NOTES_DB', str(Path(__file__).with_name('notes.sqlite3'))),
        MAX_CONTENT_LENGTH=16 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        DEBUG=False,
    )
    app.config.update(config or {})

    def connect():
        db = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        return db

    with closing(connect()) as db:
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL)')

    def token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_hex(32)
        return session['csrf']

    @app.before_request
    def protect_changes():
        if request.method in ('POST', 'PATCH', 'PUT', 'DELETE'):
            expected = session.get('csrf', '')
            supplied = request.headers.get('X-CSRF-Token', '') or request.form.get('csrf', '')
            if not expected or not secrets.compare_digest(expected.encode(), supplied.encode()):
                abort(400, description='Обнови страницу и отправь форму ещё раз: неверный CSRF-токен.')

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(413)
    @app.errorhandler(415)
    def error_response(error):
        return {'error': error.description}, error.code

    @app.after_request
    def response_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-store'
        return response

    def listing(query=''):
        with closing(connect()) as db:
            rows = db.execute('SELECT id, title FROM notes ORDER BY id DESC').fetchall()
        # Literal substring search: % and _ are ordinary text, not SQL wildcards.
        return [dict(row) for row in rows if query.casefold() in row['title'].casefold()]

    def title_from_request():
        if request.path.startswith('/api/'):
            if not request.is_json:
                abort(415, description='Нужен Content-Type application/json.')
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                abort(400, description='Нужен JSON-объект с полем title.')
        else:
            data = request.form
        try:
            return clean_title(data.get('title'))
        except ValueError as error:
            abort(400, description=str(error))

    def create(title):
        with closing(connect()) as db:
            with db:
                cursor = db.execute('INSERT INTO notes (title) VALUES (?)', (title,))
                return {'id': cursor.lastrowid, 'title': title}

    def update(note_id, title):
        with closing(connect()) as db:
            with db:
                cursor = db.execute('UPDATE notes SET title = ? WHERE id = ?', (title, note_id))
                if cursor.rowcount == 0:
                    abort(404, description='Заметка не найдена.')
        return {'id': note_id, 'title': title}

    def remove(note_id):
        with closing(connect()) as db:
            with db:
                cursor = db.execute('DELETE FROM notes WHERE id = ?', (note_id,))
                if cursor.rowcount == 0:
                    abort(404, description='Заметка не найдена.')

    @app.get('/')
    def index():
        query = request.args.get('q', '')
        return render_template_string(PAGE, notes=listing(query), query=query, token=token())

    @app.post('/notes')
    def create_form():
        create(title_from_request())
        return redirect(url_for('index'), code=303)

    @app.post('/notes/<int:note_id>/edit')
    def edit_form(note_id):
        update(note_id, title_from_request())
        return redirect(url_for('index'), code=303)

    @app.post('/notes/<int:note_id>/delete')
    def delete_form(note_id):
        remove(note_id)
        return redirect(url_for('index'), code=303)

    @app.get('/api/csrf')
    def csrf():
        return {'csrf': token()}

    @app.get('/api/notes')
    def list_api():
        return {'notes': listing(request.args.get('q', ''))}

    @app.get('/api/notes/<int:note_id>')
    def detail_api(note_id):
        with closing(connect()) as db:
            row = db.execute('SELECT id, title FROM notes WHERE id = ?', (note_id,)).fetchone()
        if row is None:
            abort(404, description='Заметка не найдена.')
        return dict(row)

    @app.post('/api/notes')
    def create_api():
        note = create(title_from_request())
        return note, 201, {'Location': url_for('detail_api', note_id=note['id'])}

    @app.patch('/api/notes/<int:note_id>')
    def update_api(note_id):
        return update(note_id, title_from_request())

    @app.delete('/api/notes/<int:note_id>')
    def delete_api(note_id):
        remove(note_id)
        return '', 204

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
