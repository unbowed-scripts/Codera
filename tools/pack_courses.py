"""Build a reproducible, compressed catalog from the authored Python records."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def pack_courses(destination):
    from curriculum_source import TRACKS, LESSONS
    from section_source import PROJECTS
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw_size = 0
    with ZipFile(destination, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        def write(name, value):
            nonlocal raw_size
            data = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            raw_size += len(data)
            info = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)

        members = {key: f'lessons/{key}.json' for key in LESSONS}
        write('index.json', dict(format=1, lessons=members,
              tracks={name: [asdict(s) for s in sections] for name, sections in TRACKS.items()}))
        for key, lesson in LESSONS.items():
            write(members[key], asdict(lesson))
        write('projects.json', PROJECTS)
    return raw_size, destination.stat().st_size


if __name__ == '__main__':
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'build/courses.zip'
    raw, packed = pack_courses(path)
    print(f'{path}: {raw:,} -> {packed:,} bytes ({100 * (1 - packed / raw):.1f}% smaller)')
