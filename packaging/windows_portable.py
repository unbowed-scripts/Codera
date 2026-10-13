"""Cross-package a portable Windows x64 app on Linux, without a Windows host.

Uses official CPython embedded runtime and PyPI Windows wheels. No pip or Python
installation is needed on the destination. Native Windows CI still builds Inno Setup.
Requires x86_64-w64-mingw32-gcc. Output is a ZIP, not an installer.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from main import VERSION
from tools.pack_courses import pack_courses


def main():
    cache = ROOT / 'build/windows-downloads'
    cache.mkdir(parents=True, exist_ok=True)
    runtime = cache / 'python-3.12.10-embed-amd64.zip'
    if not runtime.exists():
        urllib.request.urlretrieve('https://www.python.org/ftp/python/3.12.10/' + runtime.name, runtime)
    wheels = cache / 'wheels'
    subprocess.run([sys.executable, '-m', 'pip', 'download', '--only-binary=:all:',
                    '--platform', 'win_amd64', '--python-version', '312', '--implementation', 'cp',
                    '--abi', 'cp312', '--dest', str(wheels), 'PySide6-Essentials==6.8.2.1'], check=True)
    stage = ROOT / 'build/windows-portable/PythonTech'
    if stage.exists():
        shutil.rmtree(stage)
    app = stage / 'app'
    app.mkdir(parents=True)
    with zipfile.ZipFile(runtime) as archive:
        archive.extractall(app)
    for wheel in wheels.glob('*.whl'):
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(app)
    # Embedded Python searches only this application directory and its standard library.
    (app / 'python312._pth').write_text('python312.zip\n.\nimport site\n', encoding='utf-8')
    pack_courses(app / 'courses.zip')
    for name in ('main.py', 'backend.py', 'curriculum.py', 'content_models.py',
                 'content_archive.py', 'section_content.py', 'language_catalog.py',
                 'themes.py', 'ai_tutor.py', 'practice_hints.py'):
        shutil.copy2(ROOT / name, app / name)
    shutil.copytree(ROOT / 'qml', app / 'qml')
    for folder in ('web_notes', 'web_catalog', 'web_tasks'):
        destination = app / 'examples' / folder
        destination.mkdir(parents=True, exist_ok=True)
        for source in (ROOT / 'examples' / folder).iterdir():
            if source.is_file() and source.suffix in ('.py', '.md', '.txt'):
                shutil.copy2(source, destination / source.name)
    for name in ('LICENSE', 'README.md'):
        shutil.copy2(ROOT / name, stage / name)
    shutil.copy2(ROOT / 'packaging/THIRD_PARTY_NOTICES.md', stage)
    shutil.copytree(ROOT / 'build/licenses', stage / 'licenses')
    shutil.copy2(app / 'LICENSE.txt', stage / 'licenses/PYTHON-LICENSE.txt')
    (stage / 'licenses/BUILD.txt').write_text(
        'Python 3.12.10 embedded x64\nQt 6.8.2\nPySide6-Essentials / Shiboken6 6.8.2.1\n'
        'Windows portable bundle, native MinGW launcher; no PyInstaller bootloader.\n', encoding='utf-8')
    notices = stage / 'THIRD_PARTY_NOTICES.md'
    notices.write_text(notices.read_text().replace(
        'in the _internal directory', 'in the app/PySide6 directory').replace(
        '- PyInstaller bootloader, copyright PyInstaller contributors, under GPL version 2 or later with the PyInstaller bootloader exception. This exception permits distribution of bundled applications under their own license.',
        '- This portable Windows package uses the CPython embedded runtime and a native launcher; it does not include a PyInstaller bootloader.'), encoding='utf-8')
    shutil.copytree(ROOT / 'examples/habit_tracker', stage / 'examples/habit_tracker',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    subprocess.run(['x86_64-w64-mingw32-gcc', '-municode', '-mwindows', '-Os', '-s',
                    str(ROOT / 'packaging/windows_launcher.c'), '-o', str(stage / 'PythonTech.exe')], check=True)
    output = ROOT / 'dist/installers'
    output.mkdir(parents=True, exist_ok=True)
    name = output / f'PythonTech-{VERSION}-windows-x64-portable'
    shutil.make_archive(str(name), 'zip', stage.parent, stage.name)
    print(str(name) + '.zip')


if __name__ == '__main__':
    main()
