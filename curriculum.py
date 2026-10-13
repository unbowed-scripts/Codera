"""Course catalog: packaged lessons load on demand; authoring uses Python sources."""
from pathlib import Path
from content_models import Exercise, Lesson, Section
from content_archive import LessonArchive

ARCHIVE = Path(__file__).resolve().with_name('courses.zip')
if ARCHIVE.is_file():
    LESSONS = LessonArchive(ARCHIVE)
    TRACKS = LESSONS.tracks
else:
    from curriculum_source import TRACKS, LESSONS


def check_answer(exercise, answer):
    """Ignore accidental outer whitespace, preserve meaningful case and spacing."""
    return answer.strip() == exercise.answer
