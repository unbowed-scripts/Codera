"""Local learning app: accounts, per-user tasks, HTML, JSON and CSRF checks.
Public deployment also needs rate limits, HTTPS and account recovery; see README.
"""
import os
import re
import secrets
import sqlite3
from contextlib import closing
from functools import wraps
from pathlib import Path
from flask import Flask, abort, g, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

PAGE = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Мои задачи</title><h1>Мои задачи</h1>
{% if user %}<p>{{ user.username }}</p>
<form method="post" action="{{ url_for('logout') }}"><input type="hidden" name="csrf" value="{{ csrf }}"><button>Выйти</button></form>
<form method="post" action="{{ url_for('create_task') }}"><input type="hidden" name="csrf" value="{{ csrf }}">
<label>Задача <input name="title" required maxlength="120"></label><button>Добавить</button></form>
<ul>{% for task in tasks %}<li>{{ task.title }} — {{ 'готово' if task.done else 'в работе' }}
<form method="post" action="{{ url_for('toggle_task', task_id=task.id) }}"><input type="hidden" name="csrf" value="{{ csrf }}"><button>Сменить статус</button></form>
<form method="post" action="{{ url_for('delete_form', task_id=task.id) }}"><input type="hidden" name="csrf" value="{{ csrf }}"><button>Удалить</button></form></li>
{% else %}<li>Задач пока нет.</li>{% endfor %}</ul>
{% else %}<p>Учебные аккаунты: используй вымышленные данные.</p>
{% for action, label in [('register', 'Регистрация'), ('login', 'Вход')] %}
<h2>{{ label }}</h2><form method="post" action="{{ url_for(action) }}">
<input type="hidden" name="csrf" value="{{ csrf }}">
<label>Имя <input name="username" required minlength="3" maxlength="32" autocomplete="username"></label>
<label>Пароль <input name="password" type="password" required minlength="12" maxlength="128" autocomplete="{{ 'new-password' if action == 'register' else 'current-password' }}"></label>
<button>{{ label }}</button></form>{% endfor %}{% endif %}</html>'''


def clean_title(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 120:
        abort(400, description='Задача: от 1 до 120 символов')
    return value.strip()


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get('TASKS_DB', str(Path(__file__).with_name('tasks.sqlite3'))),
        SECRET_KEY=os.environ.get('TASKS_SECRET'),
        PRODUCTION=os.environ.get('TASKS_ENV') == 'production',
        MAX_CONTENT_LENGTH=16 * 1024,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', DEBUG=False)
    app.config.update(config or {})
    if app.config['PRODUCTION']:
        if not app.config['SECRET_KEY'] or len(app.config['SECRET_KEY']) < 32:
            raise ValueError('Для production задай постоянный TASKS_SECRET длиной не менее 32 символов')
        app.config['SESSION_COOKIE_SECURE'] = True
    elif not app.config['SECRET_KEY']:
        app.config['SECRET_KEY'] = secrets.token_hex(32)

    def connect():
        db = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        return db

    with closing(connect()) as db, db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id),
                title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0, 1)));
            CREATE INDEX IF NOT EXISTS tasks_owner ON tasks(owner_id);
        ''')

    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_hex(32)
        return session['csrf']

    @app.before_request
    def load_user_and_check_csrf():
        g.user = None
        if session.get('user_id') is not None:
            with closing(connect()) as db:
                g.user = db.execute('SELECT id, username FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf', '')
            expected = session.get('csrf', '')
            if not expected or not secrets.compare_digest(expected.encode(), supplied.encode()):
                abort(400, description='Токен формы неверен. Обнови страницу или запроси /api/csrf.')

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                abort(401, description='Сначала войди в аккаунт')
            return view(*args, **kwargs)
        return wrapped

    def payload():
        if request.is_json:
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                abort(400, description='Нужен JSON-объект')
            return data
        if request.mimetype not in ('application/x-www-form-urlencoded', 'multipart/form-data'):
            abort(415, description='Отправь форму или JSON')
        return request.form

    def credentials():
        data = payload()
        name, password = data.get('username'), data.get('password')
        if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9_]{3,32}', name):
            abort(400, description='Имя: 3–32 латинские буквы, цифры или подчёркивания')
        if not isinstance(password, str) or not 12 <= len(password) <= 128:
            abort(400, description='Пароль: от 12 до 128 символов')
        return name.lower(), password

    @app.get('/api/csrf')
    def csrf():
        return {'csrf': csrf_token()}

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.get('/')
    def index():
        with closing(connect()) as db:
            tasks = db.execute('SELECT id, title, done FROM tasks WHERE owner_id = ? ORDER BY id',
                               (g.user['id'],)).fetchall() if g.user else []
        return render_template_string(PAGE, user=g.user, tasks=tasks, csrf=csrf_token())

    @app.post('/auth/register')
    def register():
        name, password = credentials()
        hashed = generate_password_hash(password)
        try:
            with closing(connect()) as db, db:
                db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (name, hashed))
        except sqlite3.IntegrityError:
            abort(409, description='Это имя уже занято')
        return ({'message': 'Аккаунт создан. Теперь войди.'}, 201) if request.is_json else redirect(url_for('index'), 303)

    @app.post('/auth/login')
    def login():
        name, password = credentials()
        with closing(connect()) as db:
            user = db.execute('SELECT * FROM users WHERE username = ?', (name,)).fetchone()
        if user is None or not check_password_hash(user['password_hash'], password):
            abort(401, description='Неверное имя или пароль')
        session.clear()
        session['user_id'] = user['id']
        csrf_token()  # A new session needs a new token; old forms are rejected.
        return {'message': 'Вход выполнен'} if request.is_json else redirect(url_for('index'), 303)

    @app.post('/auth/logout')
    def logout():
        session.clear()
        return {'message': 'Выход выполнен'} if request.is_json else redirect(url_for('index'), 303)

    def owned_task(task_id):
        with closing(connect()) as db:
            task = db.execute('SELECT id, title, done FROM tasks WHERE id = ? AND owner_id = ?',
                              (task_id, g.user['id'])).fetchone()
        if task is None:
            abort(404, description='Задача не найдена')
        return task

    @app.get('/api/tasks')
    @login_required
    def list_tasks():
        with closing(connect()) as db:
            rows = db.execute('SELECT id, title, done FROM tasks WHERE owner_id = ? ORDER BY id', (g.user['id'],))
            return {'items': [dict(row) for row in rows]}

    @app.get('/api/tasks/<int:task_id>')
    @login_required
    def detail(task_id):
        return dict(owned_task(task_id))

    @app.post('/tasks')
    @app.post('/api/tasks')
    @login_required
    def create_task():
        title = clean_title(payload().get('title'))
        with closing(connect()) as db, db:
            cursor = db.execute('INSERT INTO tasks (owner_id, title) VALUES (?, ?)', (g.user['id'], title))
            task_id = cursor.lastrowid
        return ({'id': task_id, 'title': title, 'done': 0}, 201,
                {'Location': url_for('detail', task_id=task_id)}) if request.path.startswith('/api/') else redirect(url_for('index'), 303)

    @app.patch('/api/tasks/<int:task_id>')
    @login_required
    def update_task(task_id):
        task = owned_task(task_id)
        data = payload()
        if not data or set(data) - {'title', 'done'}:
            abort(400, description='Передай title и/или done')
        title = clean_title(data.get('title', task['title']))
        done = data.get('done', bool(task['done']))
        if type(done) is not bool:
            abort(400, description='done должен быть true или false')
        with closing(connect()) as db, db:
            db.execute('UPDATE tasks SET title = ?, done = ? WHERE id = ? AND owner_id = ?',
                       (title, int(done), task_id, g.user['id']))
        return dict(owned_task(task_id))

    @app.post('/tasks/<int:task_id>/toggle')
    @login_required
    def toggle_task(task_id):
        owned_task(task_id)
        with closing(connect()) as db, db:
            db.execute('UPDATE tasks SET done = 1 - done WHERE id = ? AND owner_id = ?', (task_id, g.user['id']))
        return redirect(url_for('index'), 303)

    def remove_task(task_id):
        owned_task(task_id)
        with closing(connect()) as db, db:
            db.execute('DELETE FROM tasks WHERE id = ? AND owner_id = ?', (task_id, g.user['id']))

    @app.delete('/api/tasks/<int:task_id>')
    @login_required
    def delete_task(task_id):
        remove_task(task_id)
        return '', 204

    @app.post('/tasks/<int:task_id>/delete')
    @login_required
    def delete_form(task_id):
        remove_task(task_id)
        return redirect(url_for('index'), 303)

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    @app.errorhandler(415)
    def error(error):
        return {'error': error.description}, error.code

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', debug=False)
