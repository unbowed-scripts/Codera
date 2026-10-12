# Python Web: материалы и проверка

Курс в PythonTech 0.5.0 содержит четыре раздела по шесть уроков. В каждом уроке:
теория короткими абзацами, рабочий Python-пример, объяснение, два вопроса,
самостоятельные шаги и критерии. Завершение раздела — восемь ответов теста
и мини-проект с последовательными подсказками.

Установка и обучение описаны в [README](../README.md), полный проект — в
[инструкции сервиса заметок](../examples/web_notes/README.md).

## Самостоятельная проверка материалов

Из корня проекта, после установки зависимостей приложения и Flask:

```bash
python -m unittest discover -s tests -v
python -m unittest discover -s examples/web_notes -p "test_*.py" -v
python tools/check_web_layout.py
```

Примеры уроков исполняются в отдельных временных папках; результат сравнивается
с ожидаемым выводом. Сервис заметок проверяется через test_client без сети.
Проверка интерфейса открывает все 24 урока и четыре мини-проекта на ширине
1380 и 360 пикселей, сохраняет снимки в `build/web-preview`.

## Официальные справочники

Эти ссылки нужны для дополнительного чтения; приложение не загружает их автоматически.

- [HTTP: обзор MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)
- [Клиент и сервер](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/First_steps/Client-Server_overview)
- [urllib.parse](https://docs.python.org/3/library/urllib.parse.html)
- [Flask: первые маршруты и шаблоны](https://flask.palletsprojects.com/en/stable/quickstart/)
- [Flask: работа с базой](https://flask.palletsprojects.com/en/stable/tutorial/database/)
- [sqlite3: параметры и транзакции](https://docs.python.org/3/library/sqlite3.html)
- [Flask: тестирование](https://flask.palletsprojects.com/en/stable/testing/)
- [Flask: настройки](https://flask.palletsprojects.com/en/stable/config/)
- [Flask: безопасность](https://flask.palletsprojects.com/en/stable/web-security/)
- [Flask: публикация](https://flask.palletsprojects.com/en/stable/deploying/)

Курс посвящён первому синхронному приложению Flask. Асинхронные фреймворки,
многопользовательская авторизация и эксплуатация публичного сервиса — дальнейшие темы.
