"""Run from the project root: python -m examples.habit_tracker --help."""
import argparse
from datetime import date
from pathlib import Path
from .service import add_habit, mark_habit, delete_habit
from .storage import load, save


def parser():
    result = argparse.ArgumentParser(description='Учебный трекер привычек')
    result.add_argument('--file', type=Path, default=Path('habits.json'))
    commands = result.add_subparsers(dest='command', required=True)
    add = commands.add_parser('add', help='Добавить привычку')
    add.add_argument('name')
    commands.add_parser('list', help='Показать привычки и их ID')
    mark = commands.add_parser('mark', help='Отметить день')
    mark.add_argument('id')
    mark.add_argument('--date', default=date.today().isoformat())
    delete = commands.add_parser('delete', help='Удалить привычку')
    delete.add_argument('id')
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        habits = load(args.file)
        if args.command == 'list':
            for habit in habits:
                print(f'{habit["id"]}  {habit["name"]}: {len(habit["days"])} дн.')
            if not habits:
                print('Пока нет привычек')
            return 0
        if args.command == 'add':
            habit = add_habit(habits, args.name)
            message = f'Добавлено: {habit["id"]}'
        elif args.command == 'mark':
            changed = mark_habit(habits, args.id, args.date)
            message = 'День отмечен' if changed else 'Этот день уже отмечен'
        else:
            delete_habit(habits, args.id)
            message = 'Удалено'
        save(args.file, habits)
    except (ValueError, OSError, UnicodeError) as error:
        print(f'Не удалось выполнить действие: {error}')
        return 1
    print(message)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
