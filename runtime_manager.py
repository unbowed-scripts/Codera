"""Asynchronous, user-triggered Python downloads and isolated project environments."""
import os
import sys
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot, QProcess, QProcessEnvironment, QStandardPaths


def uv_executable():
    bundled = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / 'tools' / ('uv.exe' if os.name == 'nt' else 'uv')
    if bundled.is_file(): return str(bundled)
    import uv
    return uv.find_uv_bin()


class RuntimeManager(QObject):
    changed = Signal()
    ready = Signal(str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        default = '' if getattr(sys, 'frozen', False) or Path(sys.executable).with_name('python312._pth').exists() else sys.executable
        self._python = settings.value('workspace/python', default, type=str)
        self._status = 'Выбери установленный Python или скачай Python 3.13.'
        self._log = ''
        self._step = ''
        self._cancelled = False
        self._project = None
        self._web = False
        self._prepare_after_download = None
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.process.stateChanged.connect(lambda _: self.changed.emit())
        base = QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)
        self.install_dir = Path(base) / 'python-runtimes'

    @Property(str, notify=changed)
    def python(self): return self._python

    @Property(str, notify=changed)
    def status(self): return self._status

    @Property(str, notify=changed)
    def log(self): return self._log

    @Property(bool, notify=changed)
    def busy(self): return bool(self._step)

    @Slot(str)
    def selectPython(self, value):
        if self.busy: return
        path = Path(value.strip()).expanduser()
        if not path.is_file():
            self._status = 'Файл Python не найден. Укажи полный путь к исполняемому файлу.'
            self.changed.emit()
            return
        self._candidate = str(path.resolve())
        self._run('validate', self._candidate, ['-I', '-c', 'import sys; assert sys.version_info >= (3, 10); print(sys.executable)'])

    def _run(self, step, program, args):
        self._step = step
        self._cancelled = False
        self._output = ''
        self._status = {'install': 'Скачиваем Python 3.13…', 'find': 'Ищем установленный Python…',
                        'validate': 'Проверяем Python…', 'venv': 'Создаём окружение проекта…',
                        'packages': 'Устанавливаем pip и зависимости курса…'}[step]
        env = QProcessEnvironment.systemEnvironment()
        env.insert('UV_PYTHON_INSTALL_DIR', str(self.install_dir))
        env.insert('UV_PYTHON_BIN_DIR', str(self.install_dir / 'bin'))
        env.insert('UV_PYTHON_DOWNLOADS', 'manual')
        env.insert('UV_NO_PROGRESS', '1')
        self.process.setProcessEnvironment(env)
        self.process.start(program, args)
        self.changed.emit()

    @Slot()
    def downloadPython(self):
        if self.busy: return
        try:
            self._uv = uv_executable()
            self._log = ''
            self._run('install', self._uv, ['python', 'install', '3.13', '--no-bin', '--no-registry', '--no-config'])
        except (ImportError, OSError, FileNotFoundError):
            self._status = 'Не найден uv. Переустанови зависимости приложения или выбери свой Python.'
            self.changed.emit()

    def download_for_project(self, project, web):
        if self.busy: return
        self._prepare_after_download = (project, web)
        self.downloadPython()
        if not self.busy: self._prepare_after_download = None

    @Slot()
    def cancel(self):
        if self.busy:
            self._cancelled = True
            self.process.kill()

    def _read(self):
        output = bytes(self.process.readAllStandardOutput()).decode('utf-8', errors='replace')
        self._output += output
        self._log = (self._log + output)[-24000:]
        self.changed.emit()

    def _error(self, error):
        if error == QProcess.FailedToStart:
            self._step = ''
            self._prepare_after_download = None
            self._status = 'Не удалось запустить инструмент. Проверь путь и права доступа.'
            self.changed.emit()

    def _finished(self, code, status):
        self._read()
        step, self._step = self._step, ''
        if self._cancelled:
            self._status = 'Операция отменена. Можно повторить.'
        elif code or status != QProcess.NormalExit:
            self._status = 'Операция не выполнена. Проверь журнал, сеть и свободное место; затем повтори.'
        elif step == 'install':
            self._run('find', self._uv, ['python', 'find', '3.13', '--managed-python', '--no-config'])
            return
        elif step in ('find', 'validate'):
            candidate = self._output.strip().splitlines()[-1] if self._output.strip() else ''
            if Path(candidate).is_file():
                self._python = candidate
                self.settings.setValue('workspace/python', candidate)
                self.settings.sync()
                self._status = 'Python готов: ' + candidate
                if self._prepare_after_download is not None:
                    project, web = self._prepare_after_download
                    self._prepare_after_download = None
                    self.prepare(project, web)
                    return
            else:
                self._status = 'Не удалось найти Python после установки. Выбери путь вручную.'
        elif step == 'venv':
            self._install_packages()
            return
        elif step == 'packages':
            self._status = 'Окружение проекта готово.'
            self.ready.emit(str(self._project))
        self._prepare_after_download = None
        self.changed.emit()

    @staticmethod
    def project_python(project):
        return Path(project) / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

    def prepare(self, project, web):
        if self.busy: return
        if not self._python or not Path(self._python).is_file():
            self._status = 'Сначала скачай Python или выбери установленный.'
            self.changed.emit()
            return
        self._project, self._web = Path(project), web
        self._log = ''
        try:
            self._uv = uv_executable()
            if self.project_python(self._project).is_file():
                self._install_packages()
                return
            if (self._project / '.venv').exists():
                self._status = 'Папка .venv уже есть, но Python в ней не найден. Переименуй её через файловый менеджер и повтори подготовку.'
                self.changed.emit()
                return
            self._run('venv', self._uv, ['venv', '--python', self._python, '--no-python-downloads',
                                       '--no-config', str(self._project / '.venv')])
        except (ImportError, OSError):
            self._status = 'Не найден uv. Установи зависимости приложения.'
            self.changed.emit()

    def _install_packages(self):
        packages = ['pip'] + (['Flask>=3,<4', 'requests>=2,<3'] if self._web else [])
        self._run('packages', self._uv, ['pip', 'install', '--python', str(self.project_python(self._project)),
                                       '--no-config', *packages])

    def shutdown(self):
        self.cancel()
        if self.process.state() != QProcess.NotRunning:
            self.process.waitForFinished(2000)
