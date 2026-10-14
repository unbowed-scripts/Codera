"""Qt terminal grid: keyboard/IME input, selection, scrollback and ANSI colors."""
import math
from PySide6.QtCore import Property, Signal, Slot, Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QGuiApplication
from PySide6.QtQuick import QQuickPaintedItem, QQuickItem

ANSI = dict(black='#1c2128', red='#e96d76', green='#73c991', brown='#d7ba7d',
            blue='#6cb6ff', magenta='#c4a7e7', cyan='#69cbd4', white='#d7dee7',
            brightblack='#8793a1', brightred='#ff858e', brightgreen='#a0e6b5',
            brightbrown='#ffe29b', brightblue='#a6d2ff', brightmagenta='#dfbfff',
            brightcyan='#a3eef2', brightwhite='#ffffff')


class TerminalSurface(QQuickPaintedItem):
    sessionChanged = Signal()
    appearanceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session = None
        self._appearance = None
        self._offset = 0
        self._anchor = None
        self._selection = None
        self._cell = 9.0
        self._line = 20.0
        self._rows = 24
        self._columns = 80
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setActiveFocusOnTab(True)
        self.setFlag(QQuickItem.ItemAcceptsInputMethod, True)
        self.widthChanged.connect(self._resize)
        self.heightChanged.connect(self._resize)
        self.activeFocusChanged.connect(self.update)

    @Property('QObject*', notify=sessionChanged)
    def session(self): return self._session
    @session.setter
    def session(self, session):
        if self._session is session: return
        if self._session: self._session.changed.disconnect(self._refresh)
        self._session = session
        if session: session.changed.connect(self._refresh)
        self.sessionChanged.emit()
        self._resize()

    @Property('QObject*', notify=appearanceChanged)
    def appearance(self): return self._appearance
    @appearance.setter
    def appearance(self, value):
        if self._appearance is value: return
        if self._appearance: self._appearance.changed.disconnect(self._resize)
        self._appearance = value
        if value: value.changed.connect(self._resize)
        self.appearanceChanged.emit()
        self._resize()

    def _font(self):
        font = QFont(self._appearance.fontFamily if self._appearance else 'monospace')
        font.setPixelSize(self._appearance.fontSize if self._appearance else 15)
        font.setStyleHint(QFont.Monospace)
        return font

    @Slot()
    def _resize(self):
        metrics = QFontMetricsF(self._font())
        self._cell = max(1, metrics.horizontalAdvance('M'))
        self._line = math.ceil(metrics.height()) + 2
        self._columns = max(2, min(300, int((self.width() - 24) / self._cell)))
        self._rows = max(2, min(120, int((self.height() - 20) / self._line)))
        if self._session and self.width() > 0 and self.height() > 0:
            self._session.resize(self._columns, self._rows)
        self.update()

    @Slot()
    def _refresh(self):
        if self._session and self._session.screen:
            self._offset = min(self._offset, len(self._session.screen.history.top))
        self.update()

    def _lines(self):
        if not self._session or not self._session.screen: return [], 0
        screen = self._session.screen
        lines = list(screen.history.top) + [screen.buffer[y] for y in range(screen.lines)]
        start = max(0, len(lines) - self._rows - self._offset)
        return lines[start:start+self._rows], start

    @staticmethod
    def _color(value, default):
        if value == 'default': return QColor(default)
        return QColor(ANSI.get(value, '#' + value if len(value) == 6 else default))

    def paint(self, painter):
        colors = self._appearance.colors if self._appearance else dict(background='#111418', foreground='#e6edf3', cursor='#80c7ff', selection='#284a67')
        painter.fillRect(self.boundingRect(), QColor(colors['background']))
        font = self._font()
        metrics = QFontMetricsF(font)
        lines, start = self._lines()
        bounds = sorted([self._anchor, self._selection]) if self._anchor is not None and self._selection is not None else None
        for row, cells in enumerate(lines):
            for col in range(self._columns):
                char = cells[col]
                fg, bg = self._color(char.fg, colors['foreground']), self._color(char.bg, colors['background'])
                if char.reverse: fg, bg = bg, fg
                if bounds and bounds[0] <= (row + start, col) <= bounds[1]: bg = QColor(colors['selection'])
                rectangle = QRectF(12 + col * self._cell, 10 + row * self._line, self._cell, self._line)
                if bg != QColor(colors['background']): painter.fillRect(rectangle, bg)
                font.setBold(char.bold); font.setItalic(char.italics); font.setUnderline(char.underscore)
                painter.setFont(font); painter.setPen(fg)
                painter.drawText(QPointF(rectangle.x(), rectangle.y() + metrics.ascent()), char.data)
        if self._session and self._session.screen and self._offset == 0:
            cursor = self._session.screen.cursor
            if not cursor.hidden and cursor.y < self._rows:
                rectangle = QRectF(12 + min(cursor.x, self._columns-1) * self._cell, 10 + cursor.y * self._line, 2, self._line)
                painter.fillRect(rectangle, QColor(colors['cursor']))
        if not self.hasActiveFocus():
            painter.setPen(QColor(colors['cursor']))
            painter.drawRect(QRectF(0.5, 0.5, self.width()-1, self.height()-1))

    def _send(self, value):
        self._offset = 0
        self._anchor = self._selection = None
        if self._session: self._session.send(value)
        self.update()

    def keyPressEvent(self, event):
        key, modifiers = event.key(), event.modifiers()
        ctrl = bool(modifiers & Qt.ControlModifier)
        shift = bool(modifiers & Qt.ShiftModifier)
        if ctrl and shift and key == Qt.Key_C:
            self.copySelection()
        elif ctrl and shift and key == Qt.Key_V:
            self.paste()
        elif ctrl and key in (Qt.Key_Tab, Qt.Key_Backtab):
            self.nextItemInFocusChain(not shift).forceActiveFocus(Qt.TabFocusReason)
        elif shift and key in (Qt.Key_PageUp, Qt.Key_PageDown):
            self._scroll(self._rows if key == Qt.Key_PageUp else -self._rows)
        else:
            keys = {Qt.Key_Return:'\r', Qt.Key_Enter:'\r', Qt.Key_Tab:'\t', Qt.Key_Backtab:'\x1b[Z',
                    Qt.Key_Backspace:'\x7f', Qt.Key_Escape:'\x1b', Qt.Key_Up:'\x1b[A', Qt.Key_Down:'\x1b[B',
                    Qt.Key_Right:'\x1b[C', Qt.Key_Left:'\x1b[D', Qt.Key_Home:'\x1b[H', Qt.Key_End:'\x1b[F',
                    Qt.Key_Delete:'\x1b[3~', Qt.Key_Insert:'\x1b[2~', Qt.Key_PageUp:'\x1b[5~', Qt.Key_PageDown:'\x1b[6~'}
            text = chr(key - Qt.Key_A + 1) if ctrl and Qt.Key_A <= key <= Qt.Key_Z else keys.get(key, event.text())
            if modifiers & Qt.AltModifier and text: text = '\x1b' + text
            if text: self._send(text)
            else:
                event.ignore()
                return
        event.accept()

    def inputMethodEvent(self, event):
        if event.commitString(): self._send(event.commitString())
        event.accept()

    def inputMethodQuery(self, query):
        if query == Qt.ImEnabled: return True
        if query == Qt.ImCursorRectangle: return QRectF(12, 10, self._cell, self._line)
        return super().inputMethodQuery(query)

    def _position(self, event):
        _, start = self._lines()
        return (start + max(0, min(self._rows-1, int((event.position().y()-10) / self._line))),
                max(0, min(self._columns-1, int((event.position().x()-12) / self._cell))))

    def mousePressEvent(self, event):
        self.forceActiveFocus(Qt.MouseFocusReason)
        self._anchor = self._position(event)
        self._selection = None
        event.accept()
        self.update()

    def mouseMoveEvent(self, event):
        self._selection = self._position(event)
        event.accept()
        self.update()

    def mouseReleaseEvent(self, event):
        event.accept()

    def _scroll(self, amount):
        maximum = len(self._session.screen.history.top) if self._session and self._session.screen else 0
        self._offset = min(maximum, max(0, self._offset + amount))
        self.update()

    def wheelEvent(self, event):
        self._scroll(int(event.angleDelta().y() / 40))
        event.accept()

    @Slot()
    def copySelection(self):
        if not self._session or not self._session.screen or self._selection is None or self._anchor is None: return
        screen = self._session.screen
        lines = list(screen.history.top) + [screen.buffer[y] for y in range(screen.lines)]
        first, last = sorted([self._anchor, self._selection])
        result = []
        for y in range(first[0], min(last[0]+1, len(lines))):
            left = first[1] if y == first[0] else 0
            right = last[1]+1 if y == last[0] else screen.columns
            result.append(''.join(lines[y][x].data for x in range(left, right)).rstrip())
        QGuiApplication.clipboard().setText('\n'.join(result))

    @Slot()
    def paste(self):
        self.forceActiveFocus(Qt.OtherFocusReason)
        self._offset = 0
        if self._session: self._session.paste()
