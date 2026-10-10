"""Domain rules, independent of input(), files, and any web framework."""
from datetime import date
from uuid import uuid4


def validate_habits(data):
    if not isinstance(data, list):
        raise ValueError('Ожидался список привычек')
    ids = set()
    for habit in data:
        if not isinstance(habit, dict) or set(habit) != {'id', 'name', 'days'}:
            raise ValueError('Неверные поля привычки')
        key, name, days = habit['id'], habit['name'], habit['days']
        if not isinstance(key, str) or not key.strip() or key in ids:
            raise ValueError('Неверный или повторный ID')
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Название не может быть пустым')
        if not isinstance(days, list):
            raise ValueError('Отметки должны быть списком')
        seen = set()
        for day in days:
            if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
                raise ValueError('Дата должна иметь формат YYYY-MM-DD')
            if day in seen:
                raise ValueError('Повторная дата')
            seen.add(day)
        ids.add(key)
    return data


def add_habit(habits, name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError('Название не может быть пустым')
    habit = {'id': uuid4().hex, 'name': name.strip(), 'days': []}
    habits.append(habit)
    return habit


def find_habit(habits, key):
    for habit in habits:
        if habit['id'] == key:
            return habit
    raise ValueError('Привычка с таким ID не найдена')


def mark_habit(habits, key, day):
    habit = find_habit(habits, key)
    if not isinstance(day, str):
        raise ValueError('Дата должна быть строкой YYYY-MM-DD')
    normalized = date.fromisoformat(day).isoformat()
    if normalized != day:
        raise ValueError('Дата должна иметь формат YYYY-MM-DD')
    if day in habit['days']:
        return False
    habit['days'].append(day)
    return True


def delete_habit(habits, key):
    habits.remove(find_habit(habits, key))
