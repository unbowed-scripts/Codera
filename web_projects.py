"""Web capstones: independent examples and authored code-reading assessments."""
from pathlib import Path
from web_content import WEB_CONTENT


def review(code, prompt, options, correct, explanation):
    return dict(code=code, prompt=prompt, options=options, correct=correct, explanation=explanation)


def project(title, code, walkthrough, task, criteria, hints, codes, reviews):
    return dict(title=title, code=code, walkthrough=walkthrough, task=task, criteria=criteria,
                hints=hints, hintCodes=codes, reviews=reviews)


WEB_PROJECTS = {
    'web-basics': project(
        'Инспектор локального запроса', WEB_CONTENT['web-basics/5'][1],
        '1. Сохрани пример как inspect_url.py и запусти python inspect_url.py.\n\n'
        '2. urlsplit выделяет путь и query. parse_qs возвращает значения параметров.\n\n'
        '3. int проверяет числовой формат, сравнение — диапазон.\n\n'
        '4. Код 200 обозначает принятый запрос, 400 — ошибочный параметр. Сеть не используется.',
        '1. Создай инспектор для /notes с параметрами page и limit.\n2. Поддержи только путь /notes; другой путь получает 404.\n'
        '3. page должен быть от 1 до 100, limit — от 1 до 50.\n4. Выводи результат как JSON со статусом и нормализованными параметрами.',
        '• /notes без параметров использует page=1 и limit=10.\n• /notes?page=2&limit=5 принимается.\n'
        '• Буквы, ноль и выход за границы дают 400.\n• /missing даёт 404.\n• Неверный ввод не вызывает traceback.',
        ['Разбери адрес библиотекой, затем проверь путь.', 'Преобразуй число отдельно от проверки границ.', 'Собери результат в словарь и сериализуй его.'],
        ['from urllib.parse import urlsplit\nurl = urlsplit("/notes?page=2")\nprint(url.path)',
         'raw = "5"\nlimit = int(raw)\nprint(1 <= limit <= 50)',
         'import json\nprint(json.dumps({"status": 200, "page": 2, "limit": 5}))'],
        [review('raw = parse_qs(url.query).get("page", ["1"])[0]', 'Зачем в значении по умолчанию список?',
                ['parse_qs хранит значения параметров списками.', 'HTTP всегда возвращает числа.', 'Это список всех страниц.'], 0,
                'Один параметр может повторяться. Здесь берётся первое значение или строка 1.'),
         review('if not 1 <= page <= 100:\n    return 400, "Номер вне диапазона"', 'Что проверяет условие?',
                ['Только тип строки.', 'Допустимый диапазон уже преобразованного числа.', 'Доступ к интернету.'], 1,
                'Преобразование в int не запрещает ноль и отрицательные числа. Нужна отдельная проверка границ.')]),
    'web-app': project(
        'Каталог заметок с HTML и JSON', WEB_CONTENT['web-app/5'][1],
        '1. Сохрани пример как app.py. Установи Flask: python -m pip install "Flask>=3.1,<4".\n\n'
        '2. python app.py проверяет маршруты без сети. Для браузера: python -m flask --app app run.\n\n'
        '3. /notes возвращает список, /notes/1 — запись, неизвестный id даёт 404.\n\n'
        '4. Добавь HTML через шаблон и поиск через request.args. Словарь пока используется только для чтения.',
        '1. Создай локальный каталог из трёх заметок.\n2. Покажи HTML-страницу через Jinja.\n'
        '3. Добавь поиск q и JSON-список /api/notes.\n4. Сделай страницу одной заметки с 404 для неизвестного id.',
        '• HTML и API показывают одинаковые данные.\n• Поиск без совпадений даёт пустой список, а не 404.\n'
        '• Текст <Web> отображается как текст.\n• GET не меняет каталог.\n• Маршруты проверены test_client.',
        ['Начни с обработчика, возвращающего словарь.', 'Передавай список в шаблон отдельным параметром.', 'Проверяй результат запроса локальным клиентом.'],
        [WEB_CONTENT['web-app/1'][1], WEB_CONTENT['web-app/2'][1],
         'from flask import Flask\napp = Flask(__name__)\nprint(app.test_client().get("/missing").status_code)'],
        [review('return render_template("index.html", notes=notes)', 'Как данные попадают в HTML?',
                ['notes записывается в CSS.', 'Шаблон получает переменную notes.', 'Flask автоматически создаёт базу.'], 1,
                'render_template передаёт именованный аргумент в шаблон; HTML хранится отдельно.'),
         review('note = notes.get(note_id)\nif note is None:\n    return {"error": "Не найдено"}, 404', 'Почему используется get?',
                ['Чтобы не получить KeyError для отсутствующего id.', 'Чтобы изменить запись.', 'Чтобы сохранить данные на диск.'], 0,
                'get позволяет проверить отсутствие и вернуть предусмотренный контрактом 404.')]),
    'web-data': project(
        'Хранилище заметок в SQLite', '''import sqlite3
from contextlib import closing


def save(path, title):
    title = title.strip()
    if not 1 <= len(title) <= 80:
        raise ValueError("Нужно от 1 до 80 символов")
    with closing(sqlite3.connect(path)) as db:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
            cursor = db.execute("INSERT INTO notes (title) VALUES (?)", (title,))
            return cursor.lastrowid


if __name__ == "__main__":
    note_id = save("project_notes.sqlite3", "Учусь хранить данные")
    print(note_id)
''',
        '1. save проверяет заголовок до открытия транзакции.\n\n'
        '2. База находится в project_notes.sqlite3 текущей папки. IF NOT EXISTS сохраняет существующую таблицу.\n\n'
        '3. Значение передаётся параметром; id выдаёт SQLite.\n\n'
        '4. with db фиксирует запись, closing закрывает соединение. Каждый запуск добавляет одну заметку.',
        '1. Допиши функции list_notes, update_note и delete_note.\n2. Передавай путь базы аргументом.\n'
        '3. Возвращай понятный результат для отсутствующего id.\n4. Проверь всё во временной базе, затем подключи функции к Flask.',
        '• CRUD работает по id, остальные строки не меняются.\n• Данные читаются после нового соединения.\n'
        '• Заголовок с кавычками сохраняется без ошибки.\n• Пустой заголовок не записывается.\n'
        '• Исключение откатывает транзакцию.\n• Соединения закрываются.',
        ['Передавай заголовок параметром SQL.', 'Проверяй количество изменённых строк.', 'Проверяй сохранение в отдельной временной папке.'],
        [WEB_CONTENT['web-data/2'][1], WEB_CONTENT['web-data/3'][1], WEB_CONTENT['web-quality/4'][1]],
        [review('db.execute("UPDATE notes SET title = ? WHERE id = ?", (title, note_id))', 'Для чего нужен WHERE?',
                ['Выбрать одну запись по id.', 'Закрыть базу.', 'Зашифровать заголовок.'], 0,
                'Условие ограничивает изменение. Без него UPDATE затронул бы все строки.'),
         review('with closing(sqlite3.connect(path)) as db:\n    with db:\n        db.execute(sql, params)', 'Что делает внутренний with db?',
                ['Закрывает браузер.', 'Удаляет файл базы.', 'Фиксирует транзакцию при успехе или откатывает при исключении.'], 2,
                'Закрытие соединения выполняет внешний closing; транзакцией управляет внутренний контекст.')]),
    'web-quality': project(
        'Итог: локальный сервис заметок',
        (Path(__file__).resolve().parent / 'examples' / 'web_notes' / 'app.py').read_text(encoding='utf-8'),
        '1. Установи Flask, скопируй пример в app.py и запусти python app.py. Открой http://127.0.0.1:5000/.\n\n'
        '2. create_app задаёт конфигурацию, создаёт таблицу и регистрирует HTML- и API-маршруты.\n\n'
        '3. clean_title проверяет ввод; функции create, update и remove работают через SQL-параметры и транзакции.\n\n'
        '4. Jinja экранирует текст. Все изменения требуют CSRF-токен текущей сессии; формы используют скрытое поле, API — заголовок X-CSRF-Token.\n\n'
        '5. API-клиент сначала получает GET /api/csrf, сохраняет cookie и передаёт токен при POST, PATCH и DELETE. Создание возвращает 201 и Location, удаление — 204 без тела.\n\n'
        '6. Для тестов передавай временный DATABASE в create_app. Готовые проверки: python -m unittest discover -s examples/web_notes -p "test_*.py" -v.\n\n'
        '7. Это локальный однопользовательский блокнот без входа. По умолчанию ключ сессии меняется при перезапуске: обнови страницу перед следующей отправкой. Для постоянного ключа задай NOTES_SECRET вне кода. NOTES_DB меняет путь базы.',
        '1. Запусти образец и проверь полный цикл заметки.\n2. Создай свою версию и добавь отдельное поле категории.\n'
        '3. Добавь фильтр категории, проверку её длины и тесты.\n4. Вынеси шаблон в templates/index.html, сохрани экранирование и CSRF.\n'
        '5. Подготовь инструкцию запуска и проверку после перезапуска.',
        '• Создание, просмотр, изменение и удаление работают через HTML и API.\n• Данные сохраняются после перезапуска.\n'
        '• Неверный ввод, неизвестный id и неверный токен проверены.\n• HTML пользователя не выполняется.\n'
        '• Кавычки не ломают SQL.\n• Все изменения защищены токеном; GET не меняет заметки.\n'
        '• Тесты используют временную базу.\n• Категория реализована самостоятельно и покрыта тестом.\n'
        '• Сервис остаётся на localhost, пока не добавлены вход, права доступа и настройки публикации.',
        ['Отдели проверку полей от HTTP и SQL.', 'Проверь CSRF перед изменением данных.', 'Создавай отдельное приложение и базу для тестов.'],
        ['def clean_title(value):\n    if not isinstance(value, str):\n        raise ValueError("Нужен текст")\n    value = value.strip()\n    if not 1 <= len(value) <= 80:\n        raise ValueError("От 1 до 80 символов")\n    return value\n\nprint(clean_title("  Web  "))',
         'import secrets\n\nexpected = secrets.token_hex(32)\nsupplied = expected\nvalid = secrets.compare_digest(\n    expected.encode(), supplied.encode()\n)\nprint(valid)',
         'from flask import Flask\n\ndef create_app(config):\n    app = Flask(__name__)\n    app.config.update(config)\n    return app\n\napp = create_app({"TESTING": True})\nprint(app.testing)'],
        [review('note = create(title_from_request())\nreturn note, 201, {"Location": url_for("detail_api", note_id=note["id"])}', 'Что означает ответ?',
                ['Ресурс создан; Location указывает его адрес.', 'Сервер не нашёл запись.', 'Браузер обязан повторить POST.'], 0,
                '201 сообщает о создании. Location позволяет клиенту прочитать созданную заметку.'),
         review('if not expected or not secrets.compare_digest(expected.encode(), supplied.encode()):\n    abort(400)', 'Зачем проверка перед записью?',
                ['Чтобы принять любую форму.', 'Чтобы отклонить отсутствующий или неверный CSRF-токен.', 'Чтобы зашифровать SQLite.'], 1,
                'Проверка не допускает изменение без токена текущей сессии; права доступа являются отдельной задачей.')]),
}
