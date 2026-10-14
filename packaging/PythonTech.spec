# Build on each target OS; keep Qt shared libraries replaceable in a one-folder app.
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
import uv
root = Path(SPECPATH).parent
import sys
sys.path.insert(0, str(root))
from tools.pack_courses import pack_courses
pack_courses(root / 'build/courses.zip')

a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    binaries=[(uv.find_uv_bin(), 'tools')],
    datas=[(str(root / 'build/courses.zip'), '.'),
           (str(root / 'qml'), 'qml'),
           (str(root / 'LICENSE'), '.'),
           (str(root / 'README.md'), '.'),
           (str(root / 'docs' / 'CORE_GUIDE.md'), 'docs'),
           (str(root / 'docs' / 'WEB_GUIDE.md'), 'docs'),
           (str(root / 'docs' / 'WORKSPACE.md'), 'docs'),
           (str(root / 'packaging' / 'THIRD_PARTY_NOTICES.md'), '.'),
           (str(root / 'build' / 'licenses'), 'licenses')]
          + [(str(path), f'examples/{name}')
             for name in ('web_notes', 'web_catalog', 'web_tasks')
             for path in (root / 'examples' / name).iterdir()
             if path.is_file() and path.suffix in ('.py', '.md', '.txt')]
          + [(str(path), 'examples/habit_tracker')
             for path in (root / 'examples' / 'habit_tracker').glob('*.py')],
    hiddenimports=['PySide6.QtQuick', 'PySide6.QtQuickControls2'] + collect_submodules('keyring.backends') + (collect_submodules('winpty') if sys.platform == 'win32' else []),
    excludes=['curriculum_source', 'section_source', 'core_content', 'web_content',
              'web_extended_content', 'web_projects', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
              'PySide6.QtWebEngineQuick', 'PySide6.QtCharts', 'tkinter'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='PythonTech',
          console=False, debug=False, strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PythonTech')
