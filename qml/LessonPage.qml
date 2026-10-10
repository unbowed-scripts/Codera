import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Column {
    id: page
    required property var shell
    property var lesson: backend.page
    spacing: 22
    onLessonChanged: copied.text = 'Копировать'
    AppButton { text: '←  К разделу'; quiet: true; onClicked: page.shell.navigate('section', page.lesson.sectionKey) }
    Copy { width: parent.width; text: (page.lesson.sectionTitle || '') + ' / Уровень ' + (page.lesson.index || ''); color: '#adb9b0'; font.pixelSize: 12 }
    Copy { objectName: 'pageTitle'; width: parent.width; text: page.lesson.title || ''; font.pixelSize: 32; font.weight: Font.DemiBold }
    Card {
        width: parent.width
        visible: !page.lesson.available
        height: visible ? planned.height + 48 : 0
        Column {
            id: planned
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 16
            Copy { width: parent.width; text: 'Скоро здесь будет новый урок'; font.pixelSize: 22 }
            Copy { width: parent.width; text: 'Тема включена в маршрут. Объяснение и задания пока готовятся.'; color: '#adb9b0' }
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
            Copy { width: parent.width; text: '01 / РАЗБЕРЁМСЯ'; font.pixelSize: 11; color: '#adb9b0' }
            Copy { width: parent.width; text: page.lesson.theory || ''; font.pixelSize: 16 }
            Card {
                width: parent.width; height: example.height + 40; color: '#0f1912'
                Column {
                    id: example
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                    spacing: 18
                    RowLayout {
                        width: parent.width
                        Copy { text: 'PYTHON'; color: '#adb9b0'; font.pixelSize: 11 }
                        Item { Layout.fillWidth: true }
                        AppButton { id: copied; text: 'Копировать'; quiet: true; onClicked: { backend.copyCode(); text = 'Скопировано' } }
                    }
                    Copy { width: parent.width; text: page.lesson.code || ''; color: '#b5f3c8'; font.family: 'monospace'; font.pixelSize: 14 }
                }
            }
            Copy { width: parent.width; text: page.lesson.explanation || ''; color: '#adb9b0' }
        }
    }
    Copy { visible: page.lesson.available; width: parent.width; text: 'Теперь твоя очередь'; font.pixelSize: 23; font.weight: Font.DemiBold }
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
                Copy { width: parent.width; text: 'ЗАДАНИЕ ' + (exercise.index+1); font.pixelSize: 11; color: '#adb9b0' }
                Copy { width: parent.width; text: exercise.modelData.prompt; font.pixelSize: 16 }
                TextField {
                    id: input
                    objectName: 'answer' + exercise.index
                    width: parent.width; height: 46
                    color: '#edf2ee'; placeholderTextColor: '#94a59a'; font.pixelSize: 15
                    text: exercise.modelData.answer
                    placeholderText: 'Введи свой ответ'
                    selectByMouse: true
                    Accessible.name: 'Ответ на задание ' + (exercise.index+1)
                    onTextEdited: backend.answer(page.lesson.key, exercise.index, text)
                    onAccepted: backend.check()
                    background: Rectangle { color: '#111a14'; radius: 10; border.width: input.activeFocus ? 2 : 1; border.color: exercise.feedback.text ? (exercise.feedback.ok ? '#a6efbd' : '#f0cc8c') : input.activeFocus ? '#a6efbd' : '#354039' }
                }
                // Reserve feedback space: checking an answer never shifts following content.
                Copy { width: parent.width; height: 78; text: exercise.feedback.text; color: exercise.feedback.ok ? '#a6efbd' : '#f0cc8c'; font.pixelSize: 13 }
            }
        }
    }
    Copy { objectName: 'lessonResult'; visible: page.lesson.available; width: parent.width; height: Math.max(88, implicitHeight); text: backend.feedback.message || (backend.lessonCompleted ? 'Разбор уже пройден. Можно повторить задания.' : ''); color: '#a6efbd'; font.pixelSize: 14 }
    Card {
        width: parent.width
        visible: page.lesson.available
        height: visible ? practiceContent.height + 48 : 0
        color: '#1a3022'
        Column {
            id: practiceContent
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 16
            Copy { width: parent.width; text: 'ЗАПОМНИ'; font.pixelSize: 11; color: '#a6efbd' }
            Copy { width: parent.width; text: page.lesson.remember || ''; font.pixelSize: 19 }
            Copy { width: parent.width; text: 'Напиши сам'; font.pixelSize: 22; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: page.lesson.practice || '' }
            Copy { width: parent.width; text: 'Проверь себя'; font.pixelSize: 16; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: page.lesson.criteria || ''; color: '#c0d0c5' }
            Copy { width: parent.width; text: 'Пиши в отдельном .py-файле и запускай своим Python. Здесь проверяются короткие ответы; свой код ты проверяешь по критериям выше.'; color: '#adb9b0'; font.pixelSize: 13 }
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
                    color: practiceCheck.checked ? '#a6efbd' : '#111a14'
                    border.width: practiceCheck.activeFocus ? 2 : 1
                    border.color: '#a6efbd'
                    Text { anchors.centerIn: parent; text: practiceCheck.checked ? '✓' : ''; color: '#111a14'; font.pixelSize: 16 }
                }
                contentItem: Copy {
                    leftPadding: 36
                    text: 'Написал, запустил и проверил самостоятельно'
                    font.pixelSize: 14
                }
                Accessible.name: 'Практика выполнена самостоятельно'
            }
            Copy { width: parent.width; text: 'Это твоя отметка самопроверки, а не автоматическая оценка программы.'; color: '#adb9b0'; font.pixelSize: 12 }
        }
    }
    RowLayout {
        visible: page.lesson.available; width: parent.width; spacing: 12
        AppButton { objectName: 'checkAnswers'; text: 'Проверить ответы'; primary: true; onClicked: backend.check() }
        Item { Layout.fillWidth: true }
        AppButton { objectName: 'nextLesson'; text: 'Дальше  →'; enabled: backend.lessonCompleted; onClicked: { let key = backend.nextLesson(); page.shell.navigate(key ? 'lesson' : 'section', key || page.lesson.sectionKey) } }
    }
    AppButton {
        visible: page.lesson.isCoreFinal === true
        text: 'Посмотреть маршрут Web  →'
        primary: true
        onClicked: page.shell.navigate('overview', 'Web')
    }
    Copy { visible: page.lesson.available; width: parent.width; text: 'Enter — проверить. Прогресс сохраняется на этом компьютере.'; font.pixelSize: 12; color: '#adb9b0' }
}
