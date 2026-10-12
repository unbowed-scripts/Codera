"""Build the native Qt/Python ARM64 debug APK in an isolated staging directory.

See docs/ANDROID.md for the pinned toolchain and prerequisites.
"""
import argparse
import configparser
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P4A_COMMIT = 'b92522fab879dbfc0028966ca3c59ef46ab7767d'
SOURCES = ('main.py', 'backend.py', 'curriculum.py', 'core_content.py',
           'section_content.py', 'language_catalog.py', 'themes.py', 'ai_tutor.py', 'practice_hints.py', 'web_content.py', 'web_extended_content.py', 'web_projects.py')


def run(*args, cwd):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', required=True, type=Path)
    parser.add_argument('--ndk', required=True, type=Path)
    parser.add_argument('--wheels', required=True, type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11):
        parser.error('Use Python 3.11 with PySide6==6.8.2.1 and Buildozer==1.5.0')
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
    for folder in ('web_notes', 'web_catalog', 'web_tasks'):
        example_dest = stage / 'examples' / folder
        example_dest.mkdir(parents=True, exist_ok=True)
        for source in (ROOT / 'examples' / folder).iterdir():
            if source.is_file() and source.suffix in ('.py', '.md', '.txt'):
                shutil.copy2(source, example_dest / source.name)
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
        'package.domain': 'org.pythontech', 'version': '0.6.0',
        'source.include_exts': 'py,qml,js,png,jpg,jpeg,svg,json',
        'source.exclude_dirs': '.buildozer,deployment,__pycache__',
        'requirements': 'python3==3.11.5,hostpython3==3.11.5,shiboken6,PySide6',
        'android.api': '34', 'android.minapi': '28', 'android.ndk_api': '28',
        'android.ndk': '26b', 'android.ndk_path': str(ndk),
        'android.sdk_path': str(sdk), 'android.archs': 'arm64-v8a',
        'android.permissions': 'INTERNET', 'android.debug_artifact': 'apk',
        'orientation': 'all', 'fullscreen': '0',
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
