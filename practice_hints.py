"""Small runnable examples accompanying each mini-project hint."""
PROJECT_HINT_CODES = {
    'start': [
        'name = "Саша"\nminutes_per_day = 30\ndays = 7\nprint(name, minutes_per_day, days)',
        'total = 30 * 7\nhours = total // 60\nminutes = total % 60\nprint(hours, minutes)',
        'total = 30 * 7\nassert total // 60 == 3\nassert total % 60 == 30',
    ],
    'logic': [
        'secret = 7\nguess = 5\nif guess < secret:\n    print("Нужно больше")',
        'secret = 7\nfor attempt in range(1, 6):\n    guess = int(input("Число: "))\n    if guess == secret:\n        print("Угадал!")\n        break',
        'secret = 7\nfor guess in [2, 5, 9]:\n    if guess == secret:\n        break\nelse:\n    print("Попытки закончились")',
    ],
    'collections': [
        'items = {"яблоки": 2, "хлеб": 1}\nfor name, count in items.items():\n    print(name, count)',
        'items = {"яблоки": 2}\nname = "яблоки"\nitems[name] = items.get(name, 0) + 3\nprint(items)',
        'items = {}\nfor name in ["хлеб", "хлеб"]:\n    items[name] = items.get(name, 0) + 1\nassert items["хлеб"] == 2\nitems.pop("хлеб", None)\nassert not items',
    ],
    'functions': [
        'def to_minutes(hours, minutes):\n    return hours * 60 + minutes\n\nprint(to_minutes(1, 15))',
        'def to_hours(total):\n    return total // 60, total % 60\n\ndef main():\n    hours, minutes = to_hours(75)\n    print(hours, minutes)\n\nmain()',
        'def to_minutes(hours, minutes):\n    return hours * 60 + minutes\n\nassert to_minutes(2, 5) == 125\nassert to_minutes(0, 0) == 0',
    ],
    'reliable': [
        'from pathlib import Path\n\ndef load_notes(path):\n    try:\n        return Path(path).read_text(encoding="utf-8").splitlines()\n    except FileNotFoundError:\n        return []\n\nprint(load_notes("example_notes.txt"))',
        'def append_note(path, text):\n    with open(path, "a", encoding="utf-8") as file:\n        file.write(text + "\\n")\n\nappend_note("example_notes.txt", "Повторить функции")',
        'text = input("Заметка: ").strip()\nif text:\n    with open("example_notes.txt", "a", encoding="utf-8") as file:\n        file.write(text + "\\n")\nelse:\n    print("Пустую заметку не сохраняем")',
    ],
    'idioms': [
        'sessions = {"Пн": 20, "Вт": 35}\nordered = sorted(sessions.items(), key=lambda pair: pair[1], reverse=True)\nprint(ordered)',
        'def positive(values):\n    for value in values:\n        if value > 0:\n            yield value\n\nprint(list(positive([20, 0, -5, 35])))',
        'def values():\n    yield 20\n    yield 35\n\nstream = values()\nprint(sum(stream))  # 55\nprint(list(stream))  # []\nprint(list(values()))  # новый генератор',
    ],
    'objects': [
        'from dataclasses import dataclass\n\n@dataclass\nclass Product:\n    name: str\n    price: float\n\nclass Catalog:\n    def __init__(self):\n        self.products = []',
        'from dataclasses import dataclass\n\n@dataclass\nclass Product:\n    name: str\n    price: float\n\n    def __post_init__(self):\n        if not self.name.strip() or self.price < 0:\n            raise ValueError("Проверь имя и цену")',
        'class Catalog:\n    def __init__(self):\n        self.products = []\n\nfirst = Catalog()\nsecond = Catalog()\nfirst.products.append("Книга")\nassert second.products == []',
    ],
    'tooling': [
        'import json\n\ntext = \'[{"minutes": 20}, {"minutes": 35}]\'\nsessions = json.loads(text)\nprint(sessions)',
        'def validate(data):\n    if not isinstance(data, list):\n        raise ValueError("Нужен список")\n    for item in data:\n        if not isinstance(item, dict):\n            raise ValueError("Нужен объект с minutes")\n        minutes = item.get("minutes")\n        if type(minutes) is not int or minutes < 0:\n            raise ValueError("minutes — целое неотрицательное число")',
        'def total_minutes(sessions):\n    return sum(item["minutes"] for item in sessions)\n\nassert total_minutes([{"minutes": 20}, {"minutes": 35}]) == 55\nassert total_minutes([]) == 0',
    ],
    'practice': [
        'def mark(dates, day):\n    if day not in dates:\n        dates.append(day)\n\ndates = []\nmark(dates, "2026-01-10")\nprint(dates)',
        'def mark(dates, day):\n    if day not in dates:\n        dates.append(day)\n\ndates = []\nmark(dates, "2026-01-10")\nmark(dates, "2026-01-10")\nassert len(dates) == 1',
        'from uuid import uuid4\n\nhabit = {\n    "id": str(uuid4()),\n    "name": "Читать",\n    "dates": [],\n}\nprint(habit["id"])\n# Правила отметки отдели от чтения файла.\n# При ошибке загрузки остановись до сохранения.',
    ],
}
