import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Column {
    id: page
    required property var shell
    property var lesson: backend.page
    property bool practiceHintOpen: false
    spacing: 22
    onLessonChanged: { copied.text = 'Копировать'; practiceHintOpen = false }
    AppButton { text: '←  К разделу'; quiet: true; onClicked: page.shell.navigate('section', page.lesson.sectionKey) }
    Copy { width: parent.width; text: (page.lesson.sectionTitle || '') + ' / Урок ' + (page.lesson.index || ''); color: backend.colors.muted; font.pixelSize: 12 }
    Copy { objectName: 'pageTitle'; width: parent.width; text: page.lesson.title || ''; font.pixelSize: 32; font.weight: Font.DemiBold }
    Card {
        width: parent.width
        visible: !page.lesson.available
        height: visible ? planned.height + 48 : 0
        Column {
            id: planned
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 16
            Copy { width: parent.width; text: 'Урок готовится'; font.pixelSize: 22 }
            Copy { width: parent.width; text: 'Тема есть в программе курса. Теория и задания появятся позже.'; color: backend.colors.muted }
        }
    }
    Card {
        width: parent.width
        visible: page.lesson.available
        height: visible ? theory.height + 48 : 0
        Column {
            id: theory
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 20
            Copy { width: parent.width; text: '01 / ТЕОРИЯ И ПРИМЕР'; font.pixelSize: 11; color: backend.colors.muted }
            Copy { objectName: 'lessonTheory'; width: parent.width; height: Math.max(implicitHeight, contentHeight); text: page.lesson.theory || ''; textFormat: Text.RichText; font.pixelSize: 16 }
            Card {
                width: parent.width; height: example.height + 40; color: backend.colors.code
                Column {
                    id: example
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                    spacing: 18
                    RowLayout {
                        width: parent.width
                        Copy { text: 'PYTHON'; color: backend.colors.muted; font.pixelSize: 11 }
                        Item { Layout.fillWidth: true }
                        AppButton { id: copied; text: 'Копировать'; quiet: true; onClicked: { backend.copyCode(); text = 'Скопировано' } }
                    }
                    Copy { width: parent.width; text: page.lesson.code || ''; color: backend.colors.codeText; font.family: 'monospace'; font.pixelSize: 14 }
                }
            }
            Copy { width: parent.width; text: page.lesson.explanation || ''; color: backend.colors.muted }
        }
    }
    Copy { visible: page.lesson.available; width: parent.width; text: 'Проверь понимание'; font.pixelSize: 23; font.weight: Font.DemiBold }
    Repeater {
        model: page.lesson.exercises || []
        Card {
            id: exercise
            required property var modelData
            required property int index
            property var feedback: backend.feedback.items[index] || ({ok:false, text:''})
            width: parent.width
            height: exerciseContent.height + 48
            Column {
                id: exerciseContent
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
                spacing: 14
                Copy { width: parent.width; text: 'ЗАДАНИЕ ' + (exercise.index+1); font.pixelSize: 11; color: backend.colors.muted }
                Copy { width: parent.width; text: exercise.modelData.prompt; font.pixelSize: 16 }
                TextField {
                    id: input
                    objectName: 'answer' + exercise.index
                    width: parent.width; height: 46
                    color: backend.colors.text; placeholderTextColor: backend.colors.muted; font.pixelSize: 15
                    text: exercise.modelData.answer
                    placeholderText: 'Введи свой ответ'
                    selectByMouse: true
                    Accessible.name: 'Ответ на задание ' + (exercise.index+1)
                    onTextEdited: backend.answer(page.lesson.key, exercise.index, text)
                    onAccepted: backend.check()
                    background: Rectangle { color: backend.colors.input; radius: 10; border.width: input.activeFocus ? 2 : 1; border.color: exercise.feedback.text ? (exercise.feedback.ok ? backend.colors.accent : backend.colors.warning) : input.activeFocus ? backend.colors.accent : backend.colors.border }
                }
                TutorPanel { target: 'exercise:' + exercise.index }
                // Reserve feedback space: checking an answer never shifts following content.
                Copy { width: parent.width; height: 78; text: exercise.feedback.text; color: exercise.feedback.ok ? backend.colors.accent : backend.colors.warning; font.pixelSize: 13 }
            }
        }
    }
    Copy { objectName: 'lessonResult'; visible: page.lesson.available; width: parent.width; height: Math.max(88, implicitHeight); text: backend.feedback.message || (backend.lessonCompleted ? 'Урок пройден. Задания можно повторить.' : ''); color: backend.colors.accent; font.pixelSize: 14 }
    Card {
        width: parent.width
        visible: page.lesson.available
        height: visible ? practiceContent.height + 48 : 0
        color: backend.colors.feature
        Column {
            id: practiceContent
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 16
            Copy { width: parent.width; text: 'ЗАПОМНИ'; font.pixelSize: 11; color: backend.colors.accent }
            Copy { width: parent.width; text: page.lesson.remember || ''; font.pixelSize: 19 }
            Copy { width: parent.width; text: 'Самостоятельная практика'; font.pixelSize: 22; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: page.lesson.practice || '' }
            AppButton { objectName: 'openWorkspace'; text: 'Открыть рабочее пространство'; primary: true; onClicked: backend.workspace.open('practice') }
            Copy { width: parent.width; visible: !backend.workspace.active && text.length > 0; text: backend.workspace.status; color: backend.colors.muted; font.pixelSize: 12 }
            AppButton { objectName: 'lessonPracticeHint'; text: page.practiceHintOpen ? 'Скрыть подсказку' : 'Подсказка к практике'; onClicked: page.practiceHintOpen = !page.practiceHintOpen }
            Copy { width: parent.width; visible: page.practiceHintOpen; text: '1. Вспомни правило: ' + (page.lesson.remember || '') + '\n\n2. Разбери пример: ' + (page.lesson.explanation || '') + '\n\n3. Измени пример под свою задачу. Проверь результат по критериям ниже.'; color: backend.colors.muted }
            CodeHint { objectName: 'practiceHintCode'; visible: page.practiceHintOpen; code: page.lesson.code || '' }
            TutorPanel { target: 'practice' }
            Copy { width: parent.width; text: 'Проверь себя'; font.pixelSize: 16; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: page.lesson.criteria || ''; color: backend.colors.muted }
            Copy { width: parent.width; text: 'Сохрани код в .py-файл и запусти через Python. Приложение проверяет только короткие ответы. Результат своей программы сравни с критериями выше.'; color: backend.colors.muted; font.pixelSize: 13 }
            CheckBox {
                id: practiceCheck
                objectName: 'practiceDone'
                width: parent.width
                padding: 0
                implicitHeight: Math.max(36, contentItem.implicitHeight + 12)
                checked: backend.practiceCompleted
                onToggled: backend.markPractice(checked)
                indicator: Rectangle {
                    x: 0; y: (practiceCheck.height - height) / 2
                    width: 22; height: 22; radius: 6
                    color: practiceCheck.checked ? backend.colors.accent : backend.colors.input
                    border.width: practiceCheck.activeFocus ? 2 : 1
                    border.color: backend.colors.accent
                    Text { anchors.centerIn: parent; text: practiceCheck.checked ? '✓' : ''; color: backend.colors.onAccent; font.pixelSize: 16 }
                }
                contentItem: Copy {
                    leftPadding: 36
                    text: 'Написал, запустил и проверил самостоятельно'
                    font.pixelSize: 14
                }
                Accessible.name: 'Практика выполнена самостоятельно'
            }
            Copy { width: parent.width; text: 'Отметка сохраняет результат твоей самопроверки. Приложение не оценивает этот код.'; color: backend.colors.muted; font.pixelSize: 12 }
        }
    }
    GridLayout {
        visible: page.lesson.available; width: parent.width; rowSpacing: 12; columnSpacing: 12
        columns: page.width < 500 ? 1 : 3
        AppButton { objectName: 'checkAnswers'; text: 'Проверить ответы'; primary: true; onClicked: backend.check() }
        Item { Layout.fillWidth: true }
        AppButton { objectName: 'nextLesson'; text: page.lesson.isSectionFinal ? 'К итогу раздела  →' : 'Следующий урок  →'; enabled: backend.lessonCompleted; onClicked: { if (page.lesson.isSectionFinal) { page.shell.navigate('checkpoint', page.lesson.sectionKey); return } let key = backend.nextLesson(); page.shell.navigate(key ? 'lesson' : 'section', key || page.lesson.sectionKey) } }
    }
    AppButton {
        visible: page.lesson.isCoreFinal === true
        text: 'Перейти к Python Web  →'
        primary: true
        onClicked: page.shell.navigate('overview', 'Web')
    }
    Copy { visible: page.lesson.available; width: parent.width; text: 'Enter — проверить. Прогресс сохраняется на этом компьютере.'; font.pixelSize: 12; color: backend.colors.muted }
}
