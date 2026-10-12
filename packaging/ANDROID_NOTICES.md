# Android third-party components

PythonTech is MIT licensed; see LICENSE.txt. This Android package uses Python 3.11.5, Qt 6.8.2 and PySide6/Shiboken6 6.8.2.1. License texts are included in licenses/. Language icons retain their license in qml/icons/languages/DEVICON-LICENSE.txt.

Qt and PySide6 are dynamically linked under LGPL v3. PythonTech permits replacement of these libraries with compatible modified versions and reverse engineering to debug those modifications. To install a modified APK, rebuild and sign it with your own Android key; uninstalling an existing installation may be necessary and removes its local data.

Source and rebuild information:

- Python: https://www.python.org/downloads/release/python-3115/
- Qt: https://download.qt.io/archive/qt/6.8/6.8.2/submodules/
- PySide6 and Shiboken6: https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.8.2.1-src/
- Android bootstrap and dependency recipes: https://github.com/kivy/python-for-android/tree/b92522fab879dbfc0028966ca3c59ef46ab7767d
- PythonTech build instructions: docs/ANDROID.md in the source release.

The python-for-android recipes build Python and its dependencies, including OpenSSL, SQLite and libffi, with their upstream licenses and Android patches. The APK does not use PyInstaller.
