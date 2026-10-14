"""Persistent terminal appearance, independent from the application theme."""
import hashlib
from pathlib import Path
import re
from PySide6.QtCore import QObject, Property, Signal, Slot, QSettings, QStandardPaths, QUrl
from PySide6.QtGui import QFontDatabase, QGuiApplication

THEMES = {
    'dark': dict(name='Тёмная', background='#111418', foreground='#e6edf3', cursor='#80c7ff', surface='#1c2128', border='#39424e', muted='#a8b3bf', selection='#284a67'),
    'light': dict(name='Светлая', background='#ffffff', foreground='#20252b', cursor='#005a9e', surface='#f2f4f7', border='#c3cbd4', muted='#526171', selection='#cce4ff'),
    'midnight': dict(name='Ночная', background='#17152a', foreground='#eee9ff', cursor='#c4a7ff', surface='#242039', border='#504664', muted='#bcb0d2', selection='#49356b'),
}


class TerminalPreferences(QObject):
    changed = Signal()

    def __init__(self, settings, parent=None, font_dir=None):
        super().__init__(parent)
        self.settings = settings
        self._font = settings.value('terminal/font', 'monospace', type=str)
        try: self._size = max(10, min(32, int(settings.value('terminal/fontSize', 15))))
        except (ValueError, TypeError): self._size = 15
        self._theme = settings.value('terminal/theme', 'dark', type=str)
        if self._theme not in (*THEMES, 'custom'): self._theme = 'dark'
        self._custom = {key: settings.value('terminal/' + key, THEMES['dark'][key], type=str)
                        for key in ('background', 'foreground', 'cursor')}
        for key, value in self._custom.items():
            if not self._valid_color(value): self._custom[key] = THEMES['dark'][key]
        self._status = ''
        self._font_dir = Path(font_dir) if font_dir else Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)) / 'terminal-fonts'
        self._imported = []
        # Backend-only tests can run without a GUI application.
        if isinstance(QGuiApplication.instance(), QGuiApplication):
            for path in self._font_dir.glob('*'):
                try:
                    if path.suffix.lower() in ('.ttf', '.otf') and path.stat().st_size <= 10 * 1024 * 1024:
                        font_id = QFontDatabase.addApplicationFont(str(path))
                        if font_id >= 0: self._imported.extend(QFontDatabase.applicationFontFamilies(font_id))
                except OSError:
                    continue

    @staticmethod
    def _valid_color(value): return bool(re.fullmatch(r'#[0-9a-fA-F]{6}', value))

    @Property(str, notify=changed)
    def fontFamily(self): return self._font
    @Property(int, notify=changed)
    def fontSize(self): return self._size
    @Property(str, notify=changed)
    def theme(self): return self._theme
    @Property(str, notify=changed)
    def status(self): return self._status
    @Property('QStringList', notify=changed)
    def fonts(self):
        families = ['monospace', *self._imported]
        if isinstance(QGuiApplication.instance(), QGuiApplication):
            families += [name for name in QFontDatabase.families() if QFontDatabase.isFixedPitch(name)]
        return list(dict.fromkeys([*families, self._font]))
    @Property('QVariantMap', notify=changed)
    def customColors(self): return self._custom.copy()

    @Property('QVariantMap', notify=changed)
    def colors(self):
        result = THEMES.get(self._theme, THEMES['dark']).copy()
        if self._theme == 'custom':
            result.update(self._custom)
            # Keep the controls readable for both light and dark custom backgrounds.
            rgb = [int(self._custom['background'][i:i+2], 16) for i in (1, 3, 5)]
            if sum(rgb) > 420:
                result.update({k: THEMES['light'][k] for k in ('surface', 'border', 'muted', 'selection')})
        return result

    @Slot(str, int, str, str, str, str, result=bool)
    def apply(self, family, size, theme, background, foreground, cursor):
        if family not in self.fonts or not 10 <= size <= 32 or theme not in (*THEMES, 'custom'):
            self._status = 'Выбери шрифт из списка, размер от 10 до 32 и тему.'
            self.changed.emit()
            return False
        if theme == 'custom' and not all(self._valid_color(color) for color in (background, foreground, cursor)):
            self._status = 'Укажи каждый цвет в формате #RRGGBB, например #17152a.'
            self.changed.emit()
            return False
        self._font, self._size, self._theme = family, size, theme
        if theme == 'custom':
            self._custom = dict(background=background, foreground=foreground, cursor=cursor)
        for key, value in dict(font=family, fontSize=size, theme=theme, **self._custom).items():
            self.settings.setValue('terminal/' + key, value)
        self.settings.sync()
        self._status = 'Оформление сохранено.' if self.settings.status() == QSettings.NoError else 'Оформление применено, но не сохранено. Проверь доступ к настройкам.'
        self.changed.emit()
        return True

    @Slot(str, result=bool)
    def importFont(self, value):
        path = Path(QUrl(value).toLocalFile() if value.startswith('file:') else value)
        try:
            if path.suffix.lower() not in ('.ttf', '.otf') or path.stat().st_size > 10 * 1024 * 1024:
                raise ValueError()
            raw = path.read_bytes()
            font_id = QFontDatabase.addApplicationFontFromData(raw)
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
            if not families: raise ValueError()
            self._font_dir.mkdir(parents=True, exist_ok=True)
            destination = self._font_dir / (hashlib.sha256(raw).hexdigest() + path.suffix.lower())
            destination.write_bytes(raw)
            self._imported.extend(families)
            self._font = families[0]
            self.settings.setValue('terminal/font', self._font)
            self.settings.sync()
            self._status = 'Шрифт добавлен. Для ровных колонок используй моноширинный шрифт.'
            self.changed.emit()
            return True
        except (OSError, ValueError):
            self._status = 'Не удалось добавить шрифт. Выбери исправный файл .ttf или .otf до 10 МиБ.'
            self.changed.emit()
            return False
