"""A real PTY/ConPTY session with a bounded VT screen for Qt Quick."""
import os
import queue
import signal
import threading
from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer


class PosixPtyProcess:
    """Spawn without Python callbacks after fork in Qt's multithreaded process."""
    def __init__(self, argv, cwd, env, dimensions):
        import fcntl
        import struct
        import termios
        master, slave = os.openpty()
        self.fd = master
        self._status = None
        self._closed = False
        try:
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', *dimensions, 0, 0))
            actions = [(os.POSIX_SPAWN_OPEN, 0, os.ttyname(slave), os.O_RDWR, 0),
                       (os.POSIX_SPAWN_DUP2, 0, 1), (os.POSIX_SPAWN_DUP2, 0, 2),
                       (os.POSIX_SPAWN_CLOSE, master), (os.POSIX_SPAWN_CLOSE, slave)]
            # setsid runs before opening the slave, which establishes the controlling TTY.
            # cwd and argv are positional parameters, never interpolated shell source.
            self.pid = os.posix_spawn('/bin/sh',
                ['/bin/sh', '-c', 'cd -- "$1" && shift && exec "$@"', 'pythontech-terminal', cwd, *argv],
                env, file_actions=actions, setsid=True)
            os.set_blocking(master, False)
        except Exception:
            os.close(master)
            raise
        finally:
            os.close(slave)

    def isalive(self):
        if self._status is None:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid: self._status = status
        return self._status is None

    def write(self, value): return os.write(self.fd, value)

    def setwinsize(self, rows, columns):
        import fcntl
        import struct
        import termios
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, columns, 0, 0))

    def close(self, force=True):
        if self._closed: return
        if self.isalive():
            try: os.killpg(self.pid, signal.SIGKILL if force else signal.SIGHUP)
            except ProcessLookupError: pass
            _, self._status = os.waitpid(self.pid, 0)
        os.close(self.fd)
        self._closed = True


class TerminalSession(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.screen = None
        self.stream = None
        self._text = ''
        self._running = False
        self._size = (80, 24)
        self._pending = bytearray()
        self._queue = queue.Queue(maxsize=64)
        self._stop_reader = threading.Event()
        self._reader_done = threading.Event()
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._poll)

    @Property(str, notify=changed)
    def text(self): return self._text

    @Property(bool, notify=changed)
    def running(self): return self._running

    def start(self, argv, cwd, env):
        self.stop()
        import pyte
        self.screen = pyte.HistoryScreen(*self._size, history=1000)
        self.screen.write_process_input = self.send
        self.stream = pyte.ByteStream(self.screen)
        self._queue = queue.Queue(maxsize=64)
        self._stop_reader = threading.Event()
        self._reader_done = threading.Event()
        if os.name == 'nt':
            from winpty import PtyProcess
            self.process = PtyProcess.spawn(argv, cwd=cwd, env=env,
                                            dimensions=(self._size[1], self._size[0]))
            threading.Thread(target=self._read_windows,
                             args=(self.process, self._queue, self._stop_reader, self._reader_done), daemon=True).start()
        else:
            self.process = PosixPtyProcess(argv, cwd, env, (self._size[1], self._size[0]))
        self._running = True
        self._text = ''
        self._timer.start()
        self.changed.emit()

    @staticmethod
    def _read_windows(process, output, stop, done):
        while not stop.is_set():
            try:
                data = process.read(8192)
                if not data: continue
                while not stop.is_set():
                    try:
                        output.put(data.encode('utf-8'), timeout=.1)
                        break
                    except queue.Full:
                        pass
            except (EOFError, OSError):
                break
        done.set()

    def _poll(self):
        if not self.process: return
        self._flush_input()
        data = bytearray()
        if os.name == 'nt':
            for _ in range(16):
                try: data.extend(self._queue.get_nowait())
                except queue.Empty: break
        else:
            for _ in range(16):
                try:
                    chunk = os.read(self.process.fd, 8192)
                    if not chunk: break
                    data.extend(chunk)
                except (BlockingIOError, OSError):
                    break
        if data:
            self.stream.feed(bytes(data))
            self._render()
        if not data and not self.process.isalive() and (os.name != 'nt' or self._reader_done.is_set()):
            self._running = False
            self._timer.stop()
            self._text += '\n[Терминал завершён. Нажми «Запустить терминал».]'
            self.changed.emit()

    def _render(self):
        history = [''.join(row[x].data for x in range(self.screen.columns)).rstrip()
                   for row in self.screen.history.top]
        lines = list(self.screen.display)
        cursor = self.screen.cursor
        if not cursor.hidden and 0 <= cursor.y < len(lines):
            line = lines[cursor.y]
            x = min(cursor.x, self.screen.columns - 1)
            lines[cursor.y] = line[:x] + '▏' + line[x + 1:]
        self._text = '\n'.join(history + [line.rstrip() for line in lines]).rstrip()
        self.changed.emit()

    @Slot(int, int)
    def resize(self, columns, rows):
        self._size = (max(2, min(columns, 300)), max(2, min(rows, 120)))
        if self.screen:
            self.screen.resize(lines=self._size[1], columns=self._size[0])
            if self.process and self._running:
                self.process.setwinsize(self._size[1], self._size[0])
            self._render()

    @Slot(str)
    def send(self, text):
        if self.process and self._running:
            try:
                if os.name == 'nt':
                    self.process.write(text)
                else:
                    self._pending.extend(text.encode('utf-8')[:max(0, 262144 - len(self._pending))])
                    self._flush_input()
            except (OSError, EOFError):
                self._poll()

    def _flush_input(self):
        if os.name != 'nt' and self.process and self._pending:
            try:
                count = self.process.write(self._pending[:4096])
                del self._pending[:count]
            except BlockingIOError:
                pass
            except OSError:
                self._pending.clear()

    @Slot()
    def paste(self):
        from PySide6.QtGui import QGuiApplication
        text = QGuiApplication.clipboard().text()[:64000]
        text = ''.join(c for c in text if c in '\n\t' or ord(c) >= 32).replace('\x7f', '')
        if self.screen and (2004 << 5) in self.screen.mode:
            self.send('\x1b[200~' + text + '\x1b[201~')
        else:
            self.send(text.replace('\n', '\r'))

    @Slot()
    def interrupt(self): self.send('\x03')

    @Slot()
    def stop(self):
        self._timer.stop()
        self._pending.clear()
        self._stop_reader.set()
        process, self.process = self.process, None
        self._running = False
        if process:
            import psutil
            try:
                if process.isalive():
                    try:
                        children = psutil.Process(process.pid).children(recursive=True)
                        for child in reversed(children):
                            try: child.kill()
                            except psutil.NoSuchProcess: pass
                    except psutil.Error:
                        pass
            except (OSError, EOFError):
                pass
            try:
                if os.name != 'nt':
                    # Jobs launched by an interactive shell can have separate process groups.
                    foreground = os.tcgetpgrp(process.fd)
                    if foreground > 0 and foreground != os.getpgrp():
                        try: os.killpg(foreground, signal.SIGKILL)
                        except ProcessLookupError: pass
            except (OSError, EOFError):
                pass
            try:
                process.close(force=True)
                if os.name == 'nt':
                    # pywinpty may mark closed when the child exits, before closing sockets.
                    process.fileobj.close()
                    process._server.close()
            except (OSError, EOFError):
                pass
        self.changed.emit()
