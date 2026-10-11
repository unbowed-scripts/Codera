"""Create a Debian installer and portable Linux archive from the frozen app."""
from pathlib import Path
import shutil
import subprocess
import tarfile
import sys
import platform

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from main import VERSION


def main():
    frozen = ROOT / 'dist' / 'PythonTech'
    if not (frozen / 'PythonTech').is_file():
        raise SystemExit('Build packaging/PythonTech.spec first')
    output = ROOT / 'dist' / 'installers'
    output.mkdir(parents=True, exist_ok=True)
    stage = ROOT / 'build' / 'debian'
    if stage.exists():
        shutil.rmtree(stage)
    app = stage / 'opt' / 'pythontech'
    shutil.copytree(frozen, app)
    for directory in ['DEBIAN', 'usr/bin', 'usr/share/applications']:
        (stage / directory).mkdir(parents=True, exist_ok=True)
    (stage / 'usr/bin/pythontech').symlink_to('/opt/pythontech/PythonTech')
    (stage / 'usr/share/applications/pythontech.desktop').write_text(
        '[Desktop Entry]\nType=Application\nName=PythonTech\n'
        'Comment=Learn Python with lessons and practice\n'
        'Exec=/opt/pythontech/PythonTech\nIcon=applications-education\n'
        'Terminal=false\nCategories=Education;Development;\n', encoding='utf-8')
    (stage / 'DEBIAN/control').write_text(
        f'Package: pythontech\nVersion: {VERSION}\nArchitecture: amd64\n'
        'Maintainer: PythonTech contributors <noreply@github.com>\n'
        'Section: education\nPriority: optional\n'
        f'Depends: libc6 (>= {platform.libc_ver()[1]}), libstdc++6, libgl1, libegl1, libxkbcommon0, '
        'libxkbcommon-x11-0, libxcb-cursor0, libxcb-icccm4, libxcb-image0, '
        'libxcb-keysyms1, libxcb-render-util0, libxcb-xinerama0, libxcb-randr0, '
        'libxcb-shape0, libxcb-xfixes0, libxcb-sync1, libxcb-xkb1, libdbus-1-3\n'
        'Homepage: https://github.com/unbowed-scripts/PythonTech\n'
        'Description: Offline Python learning desktop app\n'
        ' 54 Core lessons, exercises, projects and four color themes.\n', encoding='utf-8')
    subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage),
                    str(output / f'PythonTech-{VERSION}-linux-amd64.deb')], check=True)
    with tarfile.open(output / f'PythonTech-{VERSION}-linux-x64.tar.gz', 'w:gz') as archive:
        archive.add(frozen, arcname='PythonTech')


if __name__ == '__main__':
    main()
