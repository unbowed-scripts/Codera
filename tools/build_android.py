"""Build the native Qt/Python ARM64 debug APK in an isolated staging directory.

See docs/ANDROID.md for the pinned toolchain and prerequisites.
"""
import argparse
import configparser
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P4A_COMMIT = 'b92522fab879dbfc0028966ca3c59ef46ab7767d'
SOURCES = ('main.py', 'backend.py', 'curriculum.py', 'content_models.py',
           'content_archive.py', 'section_content.py', 'language_catalog.py',
           'themes.py', 'ai_tutor.py', 'practice_hints.py')


def run(*args, cwd):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', required=True, type=Path)
    parser.add_argument('--ndk', required=True, type=Path)
    parser.add_argument('--wheels', required=True, type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--version', default='0.7.0-alpha.1')
    parser.add_argument('--version-code', type=int, default=70001)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11):
        parser.error('Use Python 3.11 with PySide6==6.8.2.1 and Buildozer==1.5.0')
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.]+)?', args.version):
        parser.error('Invalid version')
    os.environ.setdefault('VIRTUAL_ENV', sys.prefix)
    sdk, ndk, wheels = args.sdk.resolve(), args.ndk.resolve(), args.wheels.resolve()
    for path in (sdk / 'platforms/android-34/android.jar', ndk / 'source.properties'):
        if not path.is_file():
            parser.error(f'Missing Android component: {path}')
    pyside = wheels / 'PySide6-6.8.2.1-6.8.2-cp311-cp311-android_aarch64.whl'
    shiboken = wheels / 'shiboken6-6.8.2.1-6.8.2-cp311-cp311-android_aarch64.whl'
    for path in (pyside, shiboken):
        if not path.is_file():
            parser.error(f'Missing Android wheel: {path}')
    stage = ROOT / 'build/android'
    stage.mkdir(parents=True, exist_ok=True)
    for name in SOURCES:
        shutil.copy2(ROOT / name, stage / name)
    from pack_courses import pack_courses
    pack_courses(stage / 'courses.zip')
    for name in ('curriculum_source', 'section_source', 'core_content', 'web_content',
                 'web_extended_content', 'web_projects'):
        (stage / f'{name}.py').unlink(missing_ok=True)
    entry = stage / 'main.py'
    entry.write_text(re.sub(r"^VERSION = .*", f"VERSION = {args.version!r}", entry.read_text(), flags=re.MULTILINE))
    for folder in ('web_notes', 'web_catalog', 'web_tasks'):
        example_dest = stage / 'examples' / folder
        example_dest.mkdir(parents=True, exist_ok=True)
        for source in (ROOT / 'examples' / folder).iterdir():
            if source.is_file() and source.suffix in ('.py', '.md', '.txt'):
                shutil.copy2(source, example_dest / source.name)
    shutil.copy2(ROOT / 'LICENSE', stage / 'LICENSE.txt')
    shutil.copy2(ROOT / 'packaging' / 'ANDROID_NOTICES.md', stage / 'THIRD_PARTY_NOTICES.md')
    if (ROOT / 'build/licenses').is_dir():
        shutil.copytree(ROOT / 'build/licenses', stage / 'licenses', dirs_exist_ok=True)
    license_dir = stage / 'licenses'
    license_dir.mkdir(exist_ok=True)
    (license_dir / 'BUILD.txt').write_text('Python 3.11.5; Qt 6.8.2; PySide6/Shiboken6 6.8.2.1; Android ARM64\n')
    # Only application assets enter the APK; no local settings, venvs or build history.
    if (stage / 'qml').exists():
        shutil.rmtree(stage / 'qml')
    shutil.copytree(ROOT / 'qml', stage / 'qml')
    deploy = Path(sys.executable).parent / 'pyside6-android-deploy'
    if not (stage / 'buildozer.spec').exists():
        run(deploy, '--init', '--name', 'PythonTech', '--wheel-pyside', pyside,
            '--wheel-shiboken', shiboken, '--ndk-path', ndk, '--sdk-path', sdk,
            '--keep-deployment-files', '-f', cwd=stage)
    config = configparser.ConfigParser()
    config.read(stage / 'buildozer.spec')
    if 'app' not in config:
        raise RuntimeError('Qt deployment did not generate buildozer.spec; inspect its output')
    config['app'].update({
        'title': 'PythonTech', 'package.name': 'pythontech',
        'package.domain': 'org.pythontech', 'version': args.version,
        'android.numeric_version': str(args.version_code),
        'source.include_exts': 'py,qml,js,png,jpg,jpeg,svg,json,md,txt,zip',
        'source.exclude_dirs': '.buildozer,deployment,__pycache__',
        'requirements': 'python3==3.11.5,hostpython3==3.11.5,shiboken6,PySide6',
        'android.api': '34', 'android.minapi': '28', 'android.ndk_api': '28',
        'android.ndk': '26b', 'android.ndk_path': str(ndk),
        'android.sdk_path': str(sdk), 'android.archs': 'arm64-v8a',
        'android.permissions': 'INTERNET', 'android.debug_artifact': 'apk',
        'android.no-byte-compile-python': '1',
        'orientation': 'portrait,landscape', 'fullscreen': '0',
        'p4a.commit': P4A_COMMIT,
    })
    destination = ROOT / 'dist/android'
    destination.mkdir(parents=True, exist_ok=True)
    config['buildozer']['bin_dir'] = str(destination)
    with (stage / 'buildozer.spec').open('w') as file:
        config.write(file)
    if args.prepare_only:
        print('Prepared Android project:', stage)
        return
    run(sys.executable, '-m', 'buildozer', 'android', 'debug', cwd=stage)
    artifacts = list(destination.glob('*.apk'))
    if not artifacts:
        raise RuntimeError('Build finished without an APK')
    print('APK:', max(artifacts, key=lambda path: path.stat().st_mtime))


if __name__ == '__main__':
    main()
