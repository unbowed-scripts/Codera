"""Validated JSON storage with atomic replacement for a single local process."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from .service import validate_habits


def load(path):
    try:
        text = Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        return []
    # Corruption is an error, never an excuse to overwrite the user's data.
    return validate_habits(json.loads(text))


def save(path, habits):
    validate_habits(habits)
    path = Path(path)
    payload = json.dumps(habits, ensure_ascii=False, indent=2) + '\n'
    temporary = None
    try:
        # Same directory keeps replace on the same filesystem.
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                prefix='.habits-', suffix='.tmp', delete=False) as file:
            temporary = Path(file.name)
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
