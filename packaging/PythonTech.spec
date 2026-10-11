# Build on each target OS; keep Qt shared libraries replaceable in a one-folder app.
from pathlib import Path
root = Path(SPECPATH).parent

a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    datas=[(str(root / 'qml'), 'qml'),
           (str(root / 'LICENSE'), '.'),
           (str(root / 'README.md'), '.'),
           (str(root / 'docs' / 'CORE_GUIDE.md'), 'docs'),
           (str(root / 'packaging' / 'THIRD_PARTY_NOTICES.md'), '.'),
           (str(root / 'build' / 'licenses'), 'licenses')]
          + [(str(path), 'examples/habit_tracker')
             for path in (root / 'examples' / 'habit_tracker').glob('*.py')],
    hiddenimports=['PySide6.QtQuick', 'PySide6.QtQuickControls2'],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
              'PySide6.QtWebEngineQuick', 'PySide6.QtCharts', 'tkinter'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='PythonTech',
          console=False, debug=False, strip=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='PythonTech')
