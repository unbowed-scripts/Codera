# Third-party components

PythonTech is MIT licensed; see LICENSE. The packaged application also contains:

- Python, copyright Python Software Foundation and contributors, under the Python license.
- Qt 6.8.2, copyright The Qt Company Ltd. and contributors. The Qt Core, Gui, Network, Qml, Quick and Quick Controls modules used here are distributed under LGPL version 3. Qt third-party components retain their respective notices in the corresponding Qt source archives.
- PySide6 / Shiboken6 6.8.2.1, copyright The Qt Company Ltd. and contributors, under LGPL version 3.
- PyInstaller bootloader, copyright PyInstaller contributors, under GPL version 2 or later with the PyInstaller bootloader exception. This exception permits distribution of bundled applications under their own license.

License texts are included in the licenses directory. Qt is dynamically linked and its shared libraries remain separate in the _internal directory. You may replace these libraries with compatible modified builds and reverse engineer for debugging such modifications as allowed by the LGPL; PythonTech imposes no additional restriction on that right.

Corresponding upstream source and build information:

- Qt: https://download.qt.io/archive/qt/6.8/6.8.2/submodules/ (qtbase, qtdeclarative, qtshadertools, qtsvg, qtwayland as applicable to the platform).
- Qt for Python: https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.8.2.1-src/ and https://doc.qt.io/qtforpython-6/building_from_source/index.html
- Python: https://www.python.org/downloads/source/ (exact interpreter version is recorded in licenses/BUILD.txt).
- PyInstaller: https://github.com/pyinstaller/pyinstaller/tree/v6.16.0

The application source, dependency versions, and packaging scripts are available at https://github.com/unbowed-scripts/PythonTech. No Qt or Python source code modifications are made by this project.
