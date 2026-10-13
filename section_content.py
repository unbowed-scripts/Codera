"""Capstones and questions for the active catalog."""
from curriculum import ARCHIVE, LESSONS, TRACKS
from content_archive import read_projects

if ARCHIVE.is_file():
    PROJECTS = read_projects(ARCHIVE)
else:
    from section_source import PROJECTS

_SECTION_COUNTS = {s.id: len(s.levels) for sections in TRACKS.values() for s in sections}


def questions(section):
    """One recall question per level plus two authored code-reading questions."""
    recall = []
    count = _SECTION_COUNTS[section]
    for index in range(1, count + 1):
        exercise = LESSONS[f'{section}/{index}'].exercises[0]
        recall.append(dict(prompt=f'Урок {index}. {exercise.prompt}', code='',
                           options=[], answer=exercise.answer, hint=exercise.hint,
                           explanation=exercise.explanation))
    return recall + [dict(item, hint='Прочитай фрагмент сверху вниз и определи роль каждого оператора.')
                     for item in PROJECTS[section]['reviews']]
