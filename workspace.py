"""Course-bound project files, manual checklists and local terminal sessions."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from PySide6.QtCore import QObject, Property, Signal, Slot, QStandardPaths, QProcess, QProcessEnvironment, QSaveFile, QIODevice, QSettings, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from terminal_session import TerminalSession
from terminal_preferences import TerminalPreferences
from runtime_manager import RuntimeManager


class Workspace(QObject):
    changed = Signal()
    editorChanged = Signal()
    terminalRequested = Signal()
    setupRequested = Signal()
    terminalWindowChanged = Signal()
    finished = Signal(str, str)

    def __init__(self, backend):
        super().__init__(backend)
        self.backend = backend
        self.settings = backend.settings
        documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation) or str(Path.home())
        self._root = self.settings.value('workspace/root', str(Path(documents) / 'PythonTech Projects'), type=str)
        self._shell = self.settings.value('workspace/shell', '', type=str)
        self._external = self.settings.value('workspace/external', '', type=str)
        self._arguments = self.settings.value('workspace/arguments', '["{project}"]', type=str)
        self._active = False
        self._project = None
        self._context = {}
        self._route = ''
        self._tasks = []
        self._checked = []
        self._files = []
        self._filename = ''
        self._content = ''
        self._original = b''
        self._dirty = False
        self._status = ''
        self._pending_launch = None
        self._terminal_window_open = False
        self._appearance = TerminalPreferences(self.settings, self)
        self._terminal = TerminalSession(self)
        self._runtime = RuntimeManager(self.settings, self)
        self._runtime.ready.connect(self._environment_ready)
        self._runtime.changed.connect(self._runtime_changed)

    @Property(bool, constant=True)
    def windowActivationSupported(self):
        return QGuiApplication.platformName() not in ('offscreen', 'minimal')

    @Property(QObject, constant=True)
    def terminalAppearance(self): return self._appearance

    @Property(bool, notify=terminalWindowChanged)
    def terminalWindowOpen(self): return self._terminal_window_open

    @Slot(bool)
    def terminalWindowVisible(self, visible):
        if self._terminal_window_open == visible: return
        self._terminal_window_open = visible
        self.terminalWindowChanged.emit()
        self._message('Терминал открыт в новом окне.' if visible else 'Окно терминала закрыто. Можно открыть новый сеанс.')

    @Slot()
    def closeTerminal(self):
        self.terminal.stop()
        self.terminalWindowVisible(False)

    @Property(QObject, constant=True)
    def terminal(self): return self._terminal
    @Property(QObject, constant=True)
    def runtime(self): return self._runtime
    @Property(bool, notify=changed)
    def active(self): return self._active
    @Property(str, notify=changed)
    def root(self): return self._root
    @Property(str, notify=changed)
    def shell(self): return self._shell
    @Property(str, notify=changed)
    def external(self): return self._external
    @Property(str, notify=changed)
    def arguments(self): return self._arguments
    @Property(str, notify=changed)
    def project(self): return str(self._project or '')
    @Property(str, notify=changed)
    def title(self): return self._context.get('title', '')
    @Property(str, notify=changed)
    def task(self): return self._context.get('task', '')
    @Property(str, notify=changed)
    def status(self): return self._status
    @Property('QVariantList', notify=changed)
    def tasks(self): return [dict(text=t, done=self._checked[i]) for i, t in enumerate(self._tasks)]
    @Property('QStringList', notify=changed)
    def files(self): return self._files
    @Property(str, notify=editorChanged)
    def filename(self): return self._filename
    @Property(str, notify=editorChanged)
    def content(self): return self._content
    @content.setter
    def content(self, text):
        if text != self._content:
            self._content = text
            self._dirty = True
            self.editorChanged.emit()
    @Property(bool, notify=editorChanged)
    def dirty(self): return self._dirty

    def _message(self, text):
        self._status = text
        self.changed.emit()

    @Slot(str, str, str, str, result=bool)
    def configure(self, root, shell, external, arguments):
        if self._active or self.runtime.busy:
            self._message('Закрой рабочее пространство и дождись окончания установки перед изменением путей.')
            return False
        try:
            path = Path(root.strip()).expanduser()
            if not root.strip() or not path.is_absolute():
                raise ValueError('Укажи полный путь к папке проектов.')
            args = json.loads(arguments)
            if not isinstance(args, list) or not all(isinstance(a, str) for a in args):
                raise ValueError('Аргументы терминала должны быть JSON-списком строк.')
            for value in (shell.strip(), external.strip()):
                if value and not self._executable(value):
                    raise ValueError('Не найден исполняемый файл терминала или оболочки.')
            self._root, self._shell, self._external, self._arguments = str(path), shell.strip(), external.strip(), arguments
            for key, value in (('root', self._root), ('shell', self._shell), ('external', self._external), ('arguments', arguments)):
                self.settings.setValue('workspace/' + key, value)
            self.settings.sync()
            self._message('Настройки сохранены.' if self.settings.status() == QSettings.NoError else 'Не удалось сохранить настройки на диск.')
            return True
        except (ValueError, OSError) as error:
            self._message(str(error))
            return False

    @staticmethod
    def _executable(value):
        return shutil.which(value) or (str(Path(value).resolve()) if Path(value).is_file() and os.access(value, os.X_OK) else '')

    @Slot(str, result=bool)
    def open(self, target):
        if self._active or self.runtime.busy: return False
        context = self.backend.tutor_context(target)
        if target not in ('practice', 'project') or context is None: return False
        route = self.backend.routeKey
        # Route IDs are stable across releases; title changes never move files.
        track = 'python-web' if context['track'] == 'Web' else 'python-core'
        folder = re.sub(r'[^a-zA-Z0-9_-]', '-', route)
        try:
            project = Path(self._root).expanduser().resolve() / track / folder
            if not project.resolve().is_relative_to(Path(self._root).expanduser().resolve()):
                raise ValueError('Папка проекта выходит за пределы выбранной папки.')
            project.mkdir(parents=True, exist_ok=True)
            for name, text in [('main.py', '# Напиши здесь своё решение.\n'),
                               ('TASK.md', context.get('task', '') + '\n\n' + context.get('criteria', ''))]:
                path = project / name
                if not path.exists():
                    with path.open('x', encoding='utf-8') as stream: stream.write(text)
            self._project, self._context, self._route = project, context, route
            self._tasks = [line.strip(' •\t') for line in context.get('criteria', '').splitlines() if line.strip()]
            if not self._tasks: self._tasks = ['Написал, запустил и проверил программу по условию.']
            saved = self.settings.value('workspace/checks/' + route, '[]', type=str)
            try: checked = json.loads(saved)
            except ValueError: checked = []
            self._checked = [task in checked for task in self._tasks]
            self._filename = ''
            self._dirty = False
            self._active = True
            self.refreshFiles()
            if not self.selectFile('main.py'):
                self._active = False
                self.changed.emit()
                return False
            self._message('Проект открыт. Подготовь окружение, затем запусти терминал. Код выполняется на твоём компьютере с твоими правами.')
            return True
        except (OSError, ValueError) as error:
            self._message('Не удалось открыть проект: ' + str(error))
            return False

    def _path(self, name):
        if not self._project or not name or Path(name).is_absolute():
            raise ValueError('Введи имя файла относительно папки проекта.')
        parts = Path(name).parts
        if any(part in ('..', '.venv', '.git') for part in parts):
            raise ValueError('Выбери учебный файл внутри проекта, вне .venv и .git.')
        path = self._project / name
        if not path.resolve().is_relative_to(self._project.resolve()):
            raise ValueError('Файл выходит за пределы проекта.')
        if any(p.is_symlink() for p in [path, *path.parents] if p != self._project.parent):
            raise ValueError('Ссылки на файлы нельзя редактировать здесь. Открой обычный файл.')
        return path

    @Slot()
    def refreshFiles(self):
        self._files = []
        if self._project:
            for root, dirs, files in os.walk(self._project):
                dirs[:] = sorted(d for d in dirs if d not in ('.venv', '.git', '__pycache__') and not (Path(root) / d).is_symlink())
                for name in sorted(files):
                    path = Path(root) / name
                    if not path.is_symlink(): self._files.append(str(path.relative_to(self._project)))
                    if len(self._files) >= 500: break
                if len(self._files) >= 500: break
        self.changed.emit()

    @Slot(str, result=bool)
    def selectFile(self, name):
        if not self.save(): return False
        try:
            path = self._path(name)
            if path.stat().st_size > 1024 * 1024: raise ValueError('Редактор открывает текстовые файлы до 1 МиБ.')
            raw = path.read_bytes()
            content = raw.decode('utf-8')
            if '\0' in content: raise ValueError('Этот файл не является текстовым.')
            self._filename, self._content, self._original, self._dirty = name, content, raw, False
            self.editorChanged.emit()
            return True
        except (OSError, ValueError) as error:
            self._message('Не удалось открыть файл: ' + str(error))
            return False

    @Slot(str, result=bool)
    def createFile(self, name):
        if not self.save(): return False
        try:
            path = self._path(name.strip())
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x', encoding='utf-8'): pass
            self.refreshFiles()
            return self.selectFile(name.strip())
        except (OSError, ValueError) as error:
            self._message('Не удалось создать файл: ' + str(error))
            return False

    @Slot(result=bool)
    def save(self):
        if not self._dirty: return True
        try:
            path = self._path(self._filename)
            if path.read_bytes() != self._original:
                raise ValueError('Файл изменён снаружи. Скопируй свой текст, затем нажми «Перечитать файл» и объедини изменения.')
            raw = self._content.encode('utf-8')
            file = QSaveFile(str(path))
            if not file.open(QIODevice.WriteOnly) or file.write(raw) != len(raw) or not file.commit():
                raise OSError('Не удалось записать файл. Проверь права и свободное место.')
            self._original, self._dirty = raw, False
            self.editorChanged.emit()
            self._message('Файл сохранён.')
            return True
        except (OSError, ValueError) as error:
            self._message(str(error))
            return False

    @Slot()
    def reloadFile(self):
        self._dirty = False
        if not self.selectFile(self._filename):
            self._dirty = True
            self.editorChanged.emit()

    @Slot(int, bool)
    def checkTask(self, index, checked):
        if not 0 <= index < len(self._checked): return
        self._checked[index] = checked
        self.settings.setValue('workspace/checks/' + self._route,
                               json.dumps([t for t, done in zip(self._tasks, self._checked) if done], ensure_ascii=False))
        self.settings.sync()
        self.changed.emit()

    def _environment(self):
        env = dict(os.environ)
        try:
            from runtime_manager import uv_executable
            env['PATH'] = str(Path(uv_executable()).parent) + os.pathsep + env.get('PATH', '')
        except (ImportError, OSError):
            pass
        env.update(TERM='xterm-256color', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
        if self._project and RuntimeManager.project_python(self._project).exists():
            venv = self._project / '.venv'
            env['VIRTUAL_ENV'] = str(venv)
            env['PATH'] = str(RuntimeManager.project_python(self._project).parent) + os.pathsep + env.get('PATH', '')
            env.pop('PYTHONHOME', None)
        return env

    @Slot()
    def prepare(self):
        if self._active and not self.terminal.running:
            self.runtime.prepare(self._project, self._context.get('track') == 'Web')
        else:
            self._message('Останови терминал перед подготовкой окружения.')

    def _ready_key(self, project):
        return 'workspace/ready/' + hashlib.sha256(str(project).encode()).hexdigest()

    def _environment_ready(self, project):
        self.settings.setValue(self._ready_key(project), True)
        if self._active and project == self.project:
            self._message('Окружение готово. Команда python использует Python этого проекта.')
            pending, self._pending_launch = self._pending_launch, None
            if pending and pending[0] == project:
                self.runFile() if pending[1] else self.startTerminal()

    def _runtime_changed(self):
        if not self.runtime.busy:
            self._pending_launch = None
        self.changed.emit()

    @Property(bool, notify=changed)
    def environmentReady(self):
        return bool(self._project and RuntimeManager.project_python(self._project).is_file()
                    and self.settings.value(self._ready_key(self.project), False, type=bool))

    @Slot(bool, bool)
    def setupAndLaunch(self, download, run_file):
        if not self._active or self.runtime.busy: return
        self._pending_launch = (self.project, run_file)
        if download:
            self.runtime.download_for_project(self._project, self._context.get('track') == 'Web')
        else:
            self.prepare()
        if not self.runtime.busy: self._pending_launch = None

    @Slot(bool)
    def requestLaunch(self, run_file):
        if not self._active or self.runtime.busy: return
        if self.environmentReady or (not run_file and self.terminal.running):
            self.runFile() if run_file else self.startTerminal()
        else:
            self.setupRequested.emit()

    @Slot()
    def startTerminal(self):
        if not self._active or self.runtime.busy: return
        if self.terminal.running:
            self.terminalRequested.emit()
            return
        shell = self._shell or (os.environ.get('COMSPEC', 'cmd.exe') if os.name == 'nt' else os.environ.get('SHELL', '/bin/sh'))
        executable = self._executable(shell)
        if not executable:
            self._message('Оболочка не найдена. Выбери её в настройках рабочего пространства.')
            return
        args = [executable]
        if Path(executable).name in ('bash', 'zsh', 'sh', 'fish'): args += ['-i']
        try:
            self.terminal.start(args, self.project, self._environment())
            self.terminalRequested.emit()
        except (ImportError, OSError, RuntimeError) as error:
            self._message('Не удалось запустить терминал: ' + str(error))

    @Slot()
    def runFile(self):
        if not self._active or self.runtime.busy or not self.save(): return
        if not self._filename.endswith('.py'):
            self._message('Выбери файл .py для запуска.')
            return
        python = RuntimeManager.project_python(self._project)
        if not python.is_file():
            self._message('Открой терминал и подготовь Python для проекта.')
            return
        try:
            # Separate PTY avoids injecting commands into a running shell/program.
            self.terminal.start([str(python), '-u', str(self._path(self._filename))], self.project, self._environment())
            self.terminalRequested.emit()
        except (OSError, ValueError, ImportError) as error:
            self._message('Не удалось запустить файл: ' + str(error))

    @Slot()
    def openFolder(self):
        if self._project: QDesktopServices.openUrl(QUrl.fromLocalFile(self.project))

    @Slot()
    def openExternal(self):
        if not self._active or self.runtime.busy or not self.save(): return
        try:
            args = json.loads(self._arguments)
            if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args): raise ValueError()
        except ValueError:
            self._message('Исправь JSON-список аргументов внешнего терминала в настройках.')
            return
        program = self._external
        args = [arg.replace('{project}', self.project) for arg in args]
        if not program:
            if os.name == 'nt':
                program, args = os.environ.get('COMSPEC', 'cmd.exe'), ['/K']
            elif sys.platform == 'darwin':
                program, args = '/usr/bin/open', ['-a', 'Terminal', self.project]
            else:
                for name, options in [('gnome-terminal', ['--working-directory', self.project]),
                                       ('konsole', ['--workdir', self.project]), ('xfce4-terminal', ['--working-directory', self.project]),
                                       ('xterm', [])]:
                    if shutil.which(name):
                        program, args = name, options
                        break
        if not program:
            self._message('Внешний терминал не найден. Укажи программу и аргументы в настройках.')
            return
        process = QProcess()
        process.setProgram(self._executable(program) or program)
        process.setArguments(args)
        process.setWorkingDirectory(self.project)
        env = QProcessEnvironment()
        for key, value in self._environment().items(): env.insert(key, value)
        process.setProcessEnvironment(env)
        ok, _ = process.startDetached()
        self._message('Внешний терминал открыт. Если он использует прежнее окружение, запускай .venv/bin/python (Windows: .venv\\Scripts\\python.exe).' if ok else 'Не удалось открыть внешний терминал. Проверь программу и аргументы.')

    @Slot(result=bool)
    def close(self):
        if not self.save(): return False
        if self.runtime.busy:
            self._message('Дождись установки или отмени её перед выходом.')
            return False
        self.closeTerminal()
        self._active = False
        self.changed.emit()
        return True

    @Slot(result=bool)
    def complete(self):
        if not self._active or self.backend.routeKey != self._route: return False
        if not all(self._checked):
            self._message('Проверь каждый критерий и отметь выполненные пункты.')
            return False
        if self.runtime.busy or not self.save(): return False
        if self.backend.kind == 'lesson':
            self.backend.markPractice(True)
            page = self.backend.page
            key = self.backend.next_keys.get(page['key'], '')
            kind = 'lesson'
            if page['isSectionFinal']:
                kind, key = 'checkpoint', page['sectionKey']
            elif not key:
                kind, key = 'section', page['sectionKey']
        else:
            self.backend.markProject(True)
            kind, key = 'overview', self.backend.track
        self.settings.sync()
        if self.settings.status() != QSettings.NoError:
            self._message('Не удалось сохранить прогресс. Проверь права и свободное место, затем повтори.')
            return False
        self.close()
        self.finished.emit(kind, key)
        return True

    def shutdown(self):
        self.terminal.stop()
        self.runtime.shutdown()
