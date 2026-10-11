"""Bundle upstream license texts before freezing the application."""
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'build' / 'licenses'
SOURCES = {
    'LGPL-3.0.txt': 'https://raw.githubusercontent.com/qt/qtbase/v6.8.2/LICENSES/LGPL-3.0-only.txt',
    'GPL-3.0.txt': 'https://raw.githubusercontent.com/qt/qtbase/v6.8.2/LICENSES/GPL-3.0-only.txt',
    'PYTHON-LICENSE.txt': f'https://raw.githubusercontent.com/python/cpython/v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}/LICENSE',
    'PYINSTALLER-LICENSE.txt': 'https://raw.githubusercontent.com/pyinstaller/pyinstaller/v6.16.0/COPYING.txt',
}

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if len(data) < 500:
            raise RuntimeError(f'Incomplete license: {name}')
        (DEST / name).write_bytes(data)
    (DEST / 'BUILD.txt').write_text(f'Python {sys.version}\nQt 6.8.2\nPySide6-Essentials 6.8.2.1\nPyInstaller 6.16.0\n', encoding='utf-8')

if __name__ == '__main__':
    main()
