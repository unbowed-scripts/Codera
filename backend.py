"""UI-independent course state exposed to Qt Quick. No animation or widget work here."""
from PySide6.QtCore import QObject, Property, Signal, Slot, QSettings
from PySide6.QtGui import QGuiApplication
from curriculum import TRACKS, LESSONS, check_answer
from section_content import PROJECTS, questions
from language_catalog import LANGUAGES, FUTURE_LANGUAGES
from themes import PALETTES, THEME_NAMES
from ai_tutor import AiTutor
from practice_hints import PROJECT_HINT_CODES

ROUTE = [
    ('Теория', 'Короткое объяснение и понятный пример.'),
    ('Разбор кода', 'Посмотри, что делает каждая строка.'),
    ('Самостоятельный разбор', 'Предскажи результат и ответь на вопросы по коду.'),
    ('Обратная связь', 'Прочитай разбор ответа. При ошибке используй подсказку.'),
    ('Практика с подсказками', 'Напиши свой код. При необходимости открой подсказку или пример.'),
    ('Читаемый код', 'Объясни, как работает твоё решение.'),
    ('Тест после раздела', 'После уроков ответь на шесть вопросов и разбери два фрагмента кода. Ошибки можно исправить.'),
    ('Мини-проект раздела', 'После теста напиши свой проект и проверь по критериям. Если нужна помощь, открой пример. Выполнение отметь самостоятельно.'),
    ('Повторение', 'Повторяй темы, когда нужно.'),
]


class Backend(QObject):
    pageChanged = Signal()
    catalogChanged = Signal()
    progressChanged = Signal()
    feedbackChanged = Signal()
    motionChanged = Signal()
    themeChanged = Signal()
    assessmentChanged = Signal()

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings if settings is not None else QSettings('PythonTech', 'Learning')
        self.completed = set(self.settings.value('completed', [], type=list)) & LESSONS.keys()
        self.practiced = set(self.settings.value('practiced', [], type=list)) & LESSONS.keys()
        self._reduced = self.settings.value('reducedMotion', False, type=bool)
        theme = self.settings.value('theme', 'green', type=str)
        self._theme = theme if theme in PALETTES else 'green'
        self.sections_by_id = {s.id: (track, s) for track, sections in TRACKS.items() for s in sections}
        self.levels = {f'{s.id}/{i}': (track, s, i, title)
                       for track, sections in TRACKS.items() for s in sections
                       for i, title in enumerate(s.levels, 1)}
        self.track_keys = {track: frozenset(key for key, info in self.levels.items() if info[0] == track)
                           for track in TRACKS}
        self.ready_keys = {track: tuple(key for key in self.levels if key in keys and key in LESSONS)
                           for track, keys in self.track_keys.items()}
        self.section_keys = {s.id: frozenset(f'{s.id}/{i}' for i in range(1, len(s.levels) + 1))
                             for sections in TRACKS.values() for s in sections}
        self.next_keys = {key: keys[index + 1] if index + 1 < len(keys) else ''
                          for keys in self.ready_keys.values() for index, key in enumerate(keys)}
        self._track = 'Python Core'
        self._kind = 'overview'
        self._key = 'Python Core'
        self.drafts = {}
        self.scrolls = {}
        self.results = {}
        self.section_tests = set(self.settings.value('sectionTests', [], type=list)) & PROJECTS.keys()
        self.section_projects = set(self.settings.value('sectionProjects', [], type=list)) & PROJECTS.keys()
        self.test_drafts = {}
        self.test_results = {}
        self._tutor = AiTutor(self)
        self.tutor_drafts = {}

    @Property(QObject, constant=True)
    def tutor(self):
        return self._tutor

    @Slot(str, str, str)
    def saveTutorDraft(self, target, code, question):
        self.tutor_drafts[self.routeKey + ':' + target] = dict(code=code, question=question)

    @Slot(str, result='QVariantMap')
    def tutorDraft(self, target):
        return self.tutor_drafts.get(self.routeKey + ':' + target, dict(code='', question=''))

    def tutor_context(self, target):
        context = dict(route=self.routeKey, track=self._track)
        if self._kind == 'lesson' and self._key in LESSONS:
            lesson = LESSONS[self._key]
            context.update(title=self.levels[self._key][3], section=self.levels[self._key][1].title,
                           theory=lesson.theory, example=lesson.code, explanation=lesson.explanation)
            if target == 'practice':
                context.update(activity='Самостоятельная практика', task=lesson.practice, criteria=lesson.criteria)
            elif target.startswith('exercise:') and target[9:].isdigit():
                index = int(target[9:])
                if not 0 <= index < len(lesson.exercises): return None
                context.update(activity='Разбор кода', question_number=index + 1,
                               task=lesson.exercises[index].prompt,
                               student_answer=self.drafts.get(self._key, [''] * len(lesson.exercises))[index])
            else: return None
        elif self._kind == 'checkpoint' and self.section_status(self._key)['unlocked']:
            context.update(section=self.sections_by_id[self._key][1].title)
            if target == 'project' and self._key in self.section_tests:
                project = PROJECTS[self._key]
                context.update(activity='Мини-проект', title=project['title'], task=project['task'],
                               example=project['code'], explanation=project['walkthrough'], criteria=project['criteria'])
            elif target.startswith('test:') and target[5:].isdigit():
                index = int(target[5:])
                tasks = questions(self._key)
                if not 0 <= index < len(tasks): return None
                task = tasks[index]
                context.update(activity='Итоговый тест', question_number=index + 1,
                               task=task['prompt'], example=task.get('code', ''), options=task['options'],
                               student_answer=self.test_drafts.get(self._key, [''] * len(tasks))[index])
            else: return None
        else: return None
        return context

    @Property('QVariantList', constant=True)
    def languages(self):
        return LANGUAGES

    @Property('QVariantList', constant=True)
    def futureLanguages(self):
        return FUTURE_LANGUAGES

    @Property(str, notify=themeChanged)
    def theme(self):
        return self._theme

    @theme.setter
    def theme(self, value):
        if value in PALETTES and value != self._theme:
            self._theme = value
            self.settings.setValue('theme', value)
            self.settings.sync()
            self.themeChanged.emit()

    @Property('QVariantMap', notify=themeChanged)
    def colors(self):
        return PALETTES[self._theme].copy()

    @Property('QVariantList', constant=True)
    def themeIds(self):
        return list(THEME_NAMES)

    @Property('QVariantList', constant=True)
    def themeNames(self):
        return list(THEME_NAMES.values())

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
                    levels=levels, count=len(levels), ready=sum(v['available'] for v in levels),
                    checkpoint=section.id in PROJECTS, **self.section_status(section.id))

    @Property('QVariantList', notify=catalogChanged)
    def sections(self):
        return [self.section(s) for s in TRACKS[self._track]]

    @Property('QVariantMap', notify=pageChanged)
    def page(self):
        if self._kind == 'checkpoint':
            project = PROJECTS[self._key]
            return dict(key=self._key, title=self.sections_by_id[self._key][1].title,
                        levelCount=len(self.sections_by_id[self._key][1].levels),
                        isTrackFinal=self._key == TRACKS[self._track][-1].id, track=self._track,
                        project={**{k: v for k, v in project.items() if k != 'reviews'},
                                 'hintCodes': project.get('hintCodes', PROJECT_HINT_CODES.get(self._key, []))},
                        questions=[{k: v for k, v in q.items() if k not in ('answer', 'correct', 'explanation', 'hint')}
                                   for q in questions(self._key)])
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
                            isSectionFinal=data['sectionKey'] in PROJECTS and data['index'] == len(self.levels[self._key][1].levels),
                            exercises=[{'prompt': e.prompt, 'answer': self.drafts.get(self._key, ['']*len(lesson.exercises))[i]}
                                       for i, e in enumerate(lesson.exercises)])
            else:
                data.update(theory='', code='', explanation='', exercises=[])
            return data
        return dict(title=self._track)

    @Property('QVariantMap', notify=progressChanged)
    def progress(self):
        keys = self.track_keys[self._track]
        ready = self.ready_keys[self._track]
        next_key = next((key for key in ready if key not in self.completed), ready[0] if ready else '')
        pending = next((section.id for section in TRACKS[self._track]
                        if section.id in PROJECTS and self.section_status(section.id)['unlocked']
                        and not (section.id in self.section_tests and section.id in self.section_projects)), '')
        project_keys = {s.id for s in TRACKS[self._track]} & PROJECTS.keys()
        return dict(checkpointTotal=len(project_keys), nextKind='checkpoint' if pending else 'lesson', continueKey=pending or next_key,
                    sectionTests=len({s.id for s in TRACKS[self._track]} & self.section_tests),
                    sectionProjects=len({s.id for s in TRACKS[self._track]} & self.section_projects),
                    done=len(keys & self.completed), total=len(keys), ready=len(ready),
                    practiced=len(keys & self.practiced),
                    webReady=self._track == 'Python Core' and keys <= (self.completed & self.practiced) and project_keys <= (self.section_tests & self.section_projects),
                    readyDone=len(set(ready) & self.completed), nextKey=next_key,
                    nextTitle=('Тест и проект: ' + self.sections_by_id[pending][1].title) if pending else self.levels[next_key][3] if next_key else 'Маршрут уже намечен',
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
                or (kind == 'checkpoint' and key in PROJECTS)
                or (kind == 'route' and key == 'guide'))

    @Property('QVariantList', notify=progressChanged)
    def completedKeys(self):
        return sorted(self.completed)

    @Slot(str, str, result=bool)
    def open(self, kind, key):
        if kind == 'overview' and key in TRACKS:
            track = key
        elif kind == 'checkpoint' and key in PROJECTS:
            track = self.sections_by_id[key][0]
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
        self._tutor.cancel()
        track_changed = track != self._track
        self._kind, self._key, self._track = kind, key, track
        if track_changed:
            self.catalogChanged.emit()
        self.pageChanged.emit()
        self.progressChanged.emit()
        self.feedbackChanged.emit()
        self.assessmentChanged.emit()
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
            message = 'Ответы верны. Выполни самостоятельную практику. ' + ('Прогресс сохранён.' if saved else 'Не удалось сохранить прогресс. Результат доступен только до закрытия приложения.')
            self.progressChanged.emit()
            self.catalogChanged.emit()
        else:
            message = 'Исправь ответы с помощью подсказок.'
        self.results[self._key] = dict(items=items, message=message, passed=passed)
        self.feedbackChanged.emit()

    @Slot(result=str)
    def nextLesson(self):
        if self._kind != 'lesson' or self._key not in self.completed:
            return ''
        return self.next_keys.get(self._key, '')

    @Slot()
    def copyCode(self):
        if self._kind == 'lesson' and self._key in LESSONS:
            QGuiApplication.clipboard().setText(LESSONS[self._key].code)

    def section_status(self, key):
        count = len(self.sections_by_id[key][1].levels)
        required = self.section_keys[key]
        return dict(levelCount=count, unlocked=key in PROJECTS and required <= self.completed,
                    levelsDone=len(required & self.completed),
                    testPassed=key in self.section_tests,
                    projectDone=key in self.section_projects)

    @Property('QVariantMap', notify=assessmentChanged)
    def assessment(self):
        if self._kind != 'checkpoint':
            return dict(unlocked=False, levelsDone=0, testPassed=False, projectDone=False,
                        answers=[], items=[], message='')
        result = self.test_results.get(self._key, dict(items=[], message=''))
        return dict(**self.section_status(self._key), **result,
                    answers=self.test_drafts.get(self._key, [''] * len(questions(self._key))))

    @Slot(int, str)
    def answerTest(self, index, value):
        if self._kind != 'checkpoint' or not self.section_status(self._key)['unlocked']:
            return
        count = len(questions(self._key))
        if not 0 <= index < count:
            return
        self.test_drafts.setdefault(self._key, [''] * count)[index] = value
        if self._key in self.test_results:
            self.test_results[self._key]['items'][index] = dict(ok=False, text='')
            self.test_results[self._key]['message'] = ''
        self.assessmentChanged.emit()

    @Slot()
    def checkTest(self):
        if self._kind != 'checkpoint' or not self.section_status(self._key)['unlocked']:
            return
        tasks = questions(self._key)
        answers = self.test_drafts.get(self._key, [''] * len(tasks))
        items = []
        for question, answer in zip(tasks, answers):
            expected = str(question['correct']) if question['options'] else question['answer']
            ok = answer.strip() == expected
            text = question['explanation'] if ok else ('Выбери или введи ответ. ' if not answer else 'Попробуй ещё раз. ') + question['hint']
            items.append(dict(ok=ok, text=text))
        passed = all(item['ok'] for item in items)
        if passed:
            self.section_tests.add(self._key)
            self.settings.setValue('sectionTests', sorted(self.section_tests))
            self.settings.sync()
        score = sum(item['ok'] for item in items)
        self.test_results[self._key] = dict(items=items, message=f'Верно: {score} / {len(items)}. ' +
            ('Тест пройден. Теперь напиши свой мини-проект.' if passed else 'Посмотри подсказки и исправь ответы. Число попыток не ограничено.'))
        self.assessmentChanged.emit()
        self.progressChanged.emit()
        self.catalogChanged.emit()

    @Slot(bool)
    def markProject(self, done):
        if (self._kind != 'checkpoint' or not self.section_status(self._key)['unlocked']
                or self._key not in self.section_tests):
            return
        if done:
            self.section_projects.add(self._key)
        else:
            self.section_projects.discard(self._key)
        self.settings.setValue('sectionProjects', sorted(self.section_projects))
        self.settings.sync()
        self.assessmentChanged.emit()
        self.progressChanged.emit()
        self.catalogChanged.emit()

    @Slot()
    def copyProject(self):
        if self._kind == 'checkpoint' and self.section_status(self._key)['unlocked']:
            QGuiApplication.clipboard().setText(PROJECTS[self._key]['code'])

    @Slot(result=str)
    def nextSection(self):
        if self._kind != 'checkpoint' or not self.section_status(self._key)['unlocked']:
            return ''
        if self._key not in self.section_tests or self._key not in self.section_projects:
            return ''
        sections = TRACKS[self._track]
        index = next(i for i, section in enumerate(sections) if section.id == self._key)
        return sections[index + 1].id if index + 1 < len(sections) else ''
