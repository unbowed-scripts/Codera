"""UI-independent course state exposed to Qt Quick. No animation or widget work here."""
from PySide6.QtCore import QObject, Property, Signal, Slot, QSettings
from PySide6.QtGui import QGuiApplication
from curriculum import TRACKS, LESSONS, check_answer

ROUTE = [
    ('Теория', 'Короткое объяснение и понятный пример.'),
    ('Разбор кода', 'Разбираемся, что делает каждая строка.'),
    ('Самостоятельный разбор', 'Пробуем предсказать результат программы.'),
    ('Обратная связь', 'Сравниваем ответ с объяснением и подсказками.'),
    ('Практика', 'Закрепляем изученное небольшими заданиями.'),
    ('Читаемый код', 'Учимся объяснять свои решения.'),
    ('Свой проект', 'Объединяем знания в работающую программу.'),
    ('Повторение', 'Возвращаемся к знакомым темам в своём темпе.'),
]


class Backend(QObject):
    pageChanged = Signal()
    catalogChanged = Signal()
    progressChanged = Signal()
    feedbackChanged = Signal()
    motionChanged = Signal()

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings if settings is not None else QSettings('PythonTech', 'Learning')
        self.completed = set(self.settings.value('completed', [], type=list)) & LESSONS.keys()
        self.practiced = set(self.settings.value('practiced', [], type=list)) & LESSONS.keys()
        self._reduced = self.settings.value('reducedMotion', False, type=bool)
        self.sections_by_id = {s.id: (track, s) for track, sections in TRACKS.items() for s in sections}
        self.levels = {f'{s.id}/{i}': (track, s, i, title)
                       for track, sections in TRACKS.items() for s in sections
                       for i, title in enumerate(s.levels, 1)}
        self._track = 'Python Core'
        self._kind = 'overview'
        self._key = 'Python Core'
        self.drafts = {}
        self.scrolls = {}
        self.results = {}

    @Property(str, notify=pageChanged)
    def kind(self):
        return self._kind

    @Property(str, notify=pageChanged)
    def track(self):
        return self._track

    @Property(str, notify=pageChanged)
    def routeKey(self):
        return f'{self._kind}:{self._key}'

    @Property('QVariantList', constant=True)
    def tracks(self):
        return list(TRACKS)

    def level(self, key):
        _, _, index, title = self.levels[key]
        return dict(key=key, index=index, title=title, available=key in LESSONS,
                    completed=key in self.completed,
                    status='Пройдено' if key in self.completed else 'Доступно' if key in LESSONS else 'Готовится')

    def section(self, section):
        levels = [self.level(f'{section.id}/{i}') for i in range(1, len(section.levels)+1)]
        return dict(key=section.id, title=section.title, outcome=section.outcome,
                    levels=levels, count=len(levels), ready=sum(v['available'] for v in levels))

    @Property('QVariantList', notify=catalogChanged)
    def sections(self):
        return [self.section(s) for s in TRACKS[self._track]]

    @Property('QVariantMap', notify=pageChanged)
    def page(self):
        if self._kind == 'section':
            return self.section(self.sections_by_id[self._key][1])
        if self._kind == 'lesson':
            data = self.level(self._key)
            data['sectionKey'] = self.levels[self._key][1].id
            data['sectionTitle'] = self.levels[self._key][1].title
            lesson = LESSONS.get(self._key)
            if lesson:
                data.update(theory=lesson.theory, code=lesson.code, explanation=lesson.explanation,
                            remember=lesson.remember, practice=lesson.practice, criteria=lesson.criteria,
                            isCoreFinal=self._key == 'practice/6',
                            exercises=[{'prompt': e.prompt, 'answer': self.drafts.get(self._key, ['']*len(lesson.exercises))[i]}
                                       for i, e in enumerate(lesson.exercises)])
            else:
                data.update(theory='', code='', explanation='', exercises=[])
            return data
        return dict(title=self._track)

    @Property('QVariantMap', notify=progressChanged)
    def progress(self):
        keys = {key for key, info in self.levels.items() if info[0] == self._track}
        ready = [key for key in self.levels if key in keys and key in LESSONS]
        next_key = next((key for key in ready if key not in self.completed), ready[0] if ready else '')
        return dict(done=len(keys & self.completed), total=len(keys), ready=len(ready),
                    practiced=len(keys & self.practiced),
                    webReady=self._track == 'Python Core' and keys <= (self.completed & self.practiced),
                    readyDone=len(set(ready) & self.completed), nextKey=next_key,
                    nextTitle=self.levels[next_key][3] if next_key else 'Маршрут уже намечен',
                    repeat=bool(ready) and set(ready) <= self.completed)

    @Property('QVariantList', constant=True)
    def route(self):
        return [dict(title=title, description=description) for title, description in ROUTE]

    @Property('QVariantMap', notify=feedbackChanged)
    def feedback(self):
        return self.results.get(self._key, dict(items=[], message='', passed=False))

    @Property(bool, notify=progressChanged)
    def lessonCompleted(self):
        return self._kind == 'lesson' and self._key in self.completed

    @Property(bool, notify=progressChanged)
    def practiceCompleted(self):
        return self._kind == 'lesson' and self._key in self.practiced

    @Slot(bool)
    def markPractice(self, done):
        if self._kind != 'lesson' or self._key not in LESSONS:
            return
        if done:
            self.practiced.add(self._key)
        else:
            self.practiced.discard(self._key)
        self.settings.setValue('practiced', sorted(self.practiced))
        self.settings.sync()
        self.progressChanged.emit()

    @Property(bool, notify=motionChanged)
    def reducedMotion(self):
        return self._reduced

    @reducedMotion.setter
    def reducedMotion(self, reduced):
        if reduced != self._reduced:
            self._reduced = reduced
            self.settings.setValue('reducedMotion', reduced)
            self.motionChanged.emit()

    @Slot(str, str, result=bool)
    def validRoute(self, kind, key):
        return ((kind == 'overview' and key in TRACKS)
                or (kind == 'section' and key in self.sections_by_id)
                or (kind == 'lesson' and key in self.levels)
                or (kind == 'route' and key == 'guide'))

    @Property('QVariantList', notify=progressChanged)
    def completedKeys(self):
        return sorted(self.completed)

    @Slot(str, str, result=bool)
    def open(self, kind, key):
        if kind == 'overview' and key in TRACKS:
            track = key
        elif kind == 'section' and key in self.sections_by_id:
            track = self.sections_by_id[key][0]
        elif kind == 'lesson' and key in self.levels:
            track = self.levels[key][0]
        elif kind == 'route':
            key, track = 'guide', self._track
        else:
            return False
        if kind == self._kind and key == self._key:
            return False
        track_changed = track != self._track
        self._kind, self._key, self._track = kind, key, track
        if track_changed:
            self.catalogChanged.emit()
        self.pageChanged.emit()
        self.progressChanged.emit()
        self.feedbackChanged.emit()
        return True

    @Slot(str, float)
    def saveScroll(self, route_key, y):
        self.scrolls[route_key] = max(0.0, y)

    @Slot(result=float)
    def restoredScroll(self):
        return self.scrolls.get(self.routeKey, 0.0)

    @Slot(str, int, str)
    def answer(self, key, index, value):
        lesson = LESSONS.get(key)
        if not lesson or not 0 <= index < len(lesson.exercises):
            return
        self.drafts.setdefault(key, [''] * len(lesson.exercises))[index] = value
        # No page/model notification while typing: input focus and geometry stay intact.
        if key in self.results:
            result = self.results[key]
            result['items'][index] = dict(ok=False, text='')
            result['message'] = ''
            self.feedbackChanged.emit()

    @Slot()
    def check(self):
        if self._kind != 'lesson' or self._key not in LESSONS:
            return
        lesson = LESSONS[self._key]
        answers = self.drafts.get(self._key, [''] * len(lesson.exercises))
        items = []
        for exercise, answer in zip(lesson.exercises, answers):
            ok = check_answer(exercise, answer)
            items.append(dict(ok=ok, text=exercise.explanation if ok else
                              ('Введи ответ. ' if not answer.strip() else 'Попробуй ещё раз. ') + exercise.hint))
        passed = all(item['ok'] for item in items)
        if passed:
            self.completed.add(self._key)
            self.settings.setValue('completed', sorted(self.completed))
            self.settings.sync()
            saved = self.settings.status() == QSettings.NoError
            message = 'Разбор пройден. Закрепи его самостоятельной практикой. ' + ('Прогресс сохранён.' if saved else 'Не удалось сохранить на диске; результат доступен до закрытия приложения.')
            self.progressChanged.emit()
        else:
            message = 'Подсказки под ответами помогут разобраться.'
        self.results[self._key] = dict(items=items, message=message, passed=passed)
        self.feedbackChanged.emit()

    @Slot(result=str)
    def nextLesson(self):
        if self._kind != 'lesson' or self._key not in self.completed:
            return ''
        track = self.levels[self._key][0]
        keys = [key for key, info in self.levels.items() if info[0] == track and key in LESSONS]
        index = keys.index(self._key)
        return keys[index + 1] if index + 1 < len(keys) else ''

    @Slot()
    def copyCode(self):
        if self._kind == 'lesson' and self._key in LESSONS:
            QGuiApplication.clipboard().setText(LESSONS[self._key].code)
