"""Read compressed lessons without extracting files or retaining the entire course."""
from collections import OrderedDict
from collections.abc import Mapping
import json
from zipfile import ZipFile

from content_models import Exercise, Lesson, Section


def read_json(path, member):
    with ZipFile(path) as archive:
        return json.loads(archive.read(member))


def read_projects(path):
    return read_json(path, 'projects.json')


class LessonArchive(Mapping):
    """Stable IDs are indexed once; at most twelve decoded lessons stay cached."""

    def __init__(self, path, cache_size=12):
        if cache_size < 1:
            raise ValueError('cache_size must be positive')
        self.path = path
        manifest = read_json(path, 'index.json')
        if manifest['format'] != 1:
            raise ValueError('Unsupported course archive format')
        self._members = manifest['lessons']
        self.tracks = {
            name: tuple(Section(**{**record, 'levels': tuple(record['levels'])})
                        for record in sections)
            for name, sections in manifest['tracks'].items()
        }
        self.cache_size = cache_size
        self._cache = OrderedDict()
        # Keep the ZIP directory indexed instead of scanning it on every cache miss.
        self._archive = ZipFile(path)

    def __len__(self):
        return len(self._members)

    def __iter__(self):
        return iter(self._members)

    def __contains__(self, key):
        return key in self._members

    def __getitem__(self, key):
        member = self._members[key]
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        record = json.loads(self._archive.read(member))
        record['exercises'] = tuple(Exercise(**item) for item in record['exercises'])
        lesson = Lesson(**record)
        self._cache[key] = lesson
        if len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)
        return lesson
