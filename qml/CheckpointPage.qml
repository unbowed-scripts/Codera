import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Column {
    id: page
    required property var shell
    property var checkpoint: backend.kind === 'checkpoint' ? backend.page : ({key:'', title:'', questions:[], project:{title:'', task:'', hints:[], code:'', walkthrough:'', criteria:''}})
    property var state: backend.assessment
    property int hintCount: 0
    property bool exampleOpen: false
    spacing: 20
    onCheckpointChanged: { hintCount = 0; exampleOpen = false }
    AppButton { text: '←  К разделу'; quiet: true; onClicked: page.shell.navigate('section', page.checkpoint.key) }
    Copy { width: parent.width; text: 'ПОСЛЕ ШЕСТИ УРОВНЕЙ'; font.pixelSize: 11; color: backend.colors.accent }
    Copy { objectName: 'pageTitle'; width: parent.width; text: 'Тест и мини-проект'; font.pixelSize: 32; font.weight: Font.DemiBold }
    Copy { width: parent.width; text: page.checkpoint.title || ''; font.pixelSize: 20 }
    Copy {
        objectName: 'checkpointStatus'
        width: parent.width
        text: !page.state.unlocked ? 'Пройдено ' + page.state.levelsDone + ' / 6 уровней. Заверши разбор заданий во всех шести уроках, чтобы открыть тест и проект.' : page.state.testPassed && page.state.projectDone ? 'Раздел завершён: тест пройден, свой проект отмечен как выполненный.' : page.state.testPassed ? 'Тест уже пройден. Осталось написать и проверить свой проект.' : 'Сначала проверь знания, затем собери свою программу. Ответы можно исправлять, а подсказки открывать по мере необходимости.'
        color: backend.colors.muted
    }
    Column {
        visible: page.state.unlocked
        width: parent.width
        spacing: 20
        Copy { width: parent.width; text: '01 / Итоговый тест'; font.pixelSize: 23; font.weight: Font.DemiBold }
        Copy { width: parent.width; text: 'Шесть коротких вопросов — по одному на каждый уровень. Затем два фрагмента кода: выбери, что означают их части. Для прохождения нужны 8 верных ответов.'; color: backend.colors.muted }
        Repeater {
            model: page.state.unlocked ? page.checkpoint.questions : []
            Card {
                id: question
                required property var modelData
                required property int index
                property var result: page.state.items[index] || ({ok:false, text:''})
                width: parent.width
                height: body.height + 40
                Column {
                    id: body
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                    spacing: 14
                    Copy { width: parent.width; text: 'ВОПРОС ' + (question.index + 1); color: backend.colors.muted; font.pixelSize: 11 }
                    Copy { width: parent.width; text: question.modelData.prompt; font.pixelSize: 16 }
                    Copy { visible: text.length > 0; width: parent.width; text: question.modelData.code || ''; font.family: 'monospace'; color: backend.colors.codeText }
                    TextField {
                        objectName: 'testAnswer' + question.index
                        visible: question.modelData.options.length === 0
                        width: parent.width; height: 46
                        text: page.state.answers[question.index] || ''
                        placeholderText: 'Введи короткий ответ'
                        selectByMouse: true
                        color: backend.colors.text
                        placeholderTextColor: backend.colors.muted
                        font.pixelSize: 15
                        Accessible.name: 'Ответ на вопрос ' + (question.index + 1)
                        onTextEdited: backend.answerTest(question.index, text)
                        onAccepted: backend.checkTest()
                        background: Rectangle { radius: 10; color: backend.colors.input; border.width: parent.activeFocus ? 2 : 1; border.color: parent.activeFocus ? backend.colors.accent : backend.colors.border }
                    }
                    Repeater {
                        model: question.modelData.options
                        RadioButton {
                            id: option
                            required property string modelData
                            required property int index
                            objectName: 'testOption' + question.index + '_' + index
                            width: parent.width
                            implicitHeight: Math.max(48, contentItem.implicitHeight + 20)
                            checked: page.state.answers[question.index] === String(index)
                            autoExclusive: false
                            onClicked: backend.answerTest(question.index, String(index))
                            focusPolicy: Qt.StrongFocus
                            Accessible.name: modelData
                            indicator: Rectangle {
                                x: 12; y: (option.height - height) / 2; width: 20; height: 20; radius: 10
                                color: 'transparent'; border.color: backend.colors.accent
                                Rectangle { anchors.centerIn: parent; width: 10; height: 10; radius: 5; visible: option.checked; color: backend.colors.accent }
                            }
                            contentItem: Copy { leftPadding: 44; rightPadding: 12; text: option.modelData; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 10; color: option.checked ? backend.colors.selected : backend.colors.input; border.width: option.activeFocus ? 2 : 1; border.color: option.activeFocus ? backend.colors.accent : backend.colors.border }
                        }
                    }
                    Copy { width: parent.width; visible: text.length > 0; text: question.result.text; color: question.result.ok ? backend.colors.accent : backend.colors.warning }
                }
            }
        }
        AppButton { objectName: 'checkSectionTest'; text: 'Проверить тест'; primary: true; onClicked: backend.checkTest() }
        Copy { objectName: 'sectionTestResult'; width: parent.width; text: page.state.message || ''; visible: text.length > 0; color: backend.colors.accent }
        Copy { width: parent.width; text: '02 / Мини-проект'; font.pixelSize: 23; font.weight: Font.DemiBold }
        Copy { width: parent.width; visible: !page.state.testPassed; text: 'Мини-проект откроется после успешного теста. Разбор каждого ответа поможет подготовиться.'; color: backend.colors.muted }
        Column {
            width: parent.width
            visible: page.state.testPassed
            spacing: 18
            Copy { width: parent.width; text: page.checkpoint.project.title; font.pixelSize: 22; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: 'Твоя задача'; font.pixelSize: 18; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: page.checkpoint.project.task }
            Copy { width: parent.width; text: 'Пиши в отдельном .py-файле и запускай своим Python. Сначала попробуй сам. Если застрянешь, открой подсказку или готовый пример ниже.'; color: backend.colors.muted }
            AppButton {
                objectName: 'projectHint'
                text: page.hintCount === 0 ? 'Показать подсказку' : 'Следующая подсказка'
                enabled: page.hintCount < page.checkpoint.project.hints.length
                onClicked: page.hintCount++
            }
            Repeater {
                model: page.hintCount
                Copy { required property int index; width: parent.width; text: (index + 1) + '. ' + page.checkpoint.project.hints[index]; color: backend.colors.accent }
            }
            AppButton { objectName: 'showProjectExample'; text: page.exampleOpen ? 'Скрыть пример и разбор' : 'Готовый пример и разбор'; onClicked: page.exampleOpen = !page.exampleOpen }
            Column {
                visible: page.exampleOpen
                width: parent.width
                spacing: 16
                Copy { width: parent.width; text: 'Учебный пример'; font.pixelSize: 18; font.weight: Font.DemiBold }
                Copy { width: parent.width; text: 'Сохрани пример в отдельный файл, запусти и сравни результат с разбором. Затем закрой пример и создай свою версию по заданию выше.'; color: backend.colors.muted }
                AppButton { objectName: 'copyProject'; text: 'Копировать пример'; onClicked: { backend.copyProject(); text = 'Скопировано' } }
                Card {
                    width: parent.width; height: exampleCode.height + 32; color: backend.colors.code
                    Copy { id: exampleCode; objectName: 'projectCode'; anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 } text: page.checkpoint.project.code; font.family: 'monospace'; font.pixelSize: 14; color: backend.colors.codeText }
                }
                Copy { width: parent.width; text: 'Что делает каждая часть'; font.pixelSize: 18; font.weight: Font.DemiBold }
                Copy { width: parent.width; text: page.checkpoint.project.walkthrough }
            }
            Copy { width: parent.width; text: 'Проверь свою версию'; font.pixelSize: 18; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: page.checkpoint.project.criteria }
            CheckBox {
                id: done
                objectName: 'sectionProjectDone'
                width: parent.width
                implicitHeight: Math.max(48, contentItem.implicitHeight + 16)
                checked: page.state.projectDone
                onToggled: backend.markProject(checked)
                Accessible.name: 'Свой проект написан, запущен и проверен'
                indicator: Rectangle {
                    y: (done.height - height) / 2; width: 24; height: 24; radius: 6
                    color: done.checked ? backend.colors.accent : backend.colors.input
                    border.color: done.activeFocus ? backend.colors.text : backend.colors.accent
                    border.width: done.activeFocus ? 2 : 1
                    Text { anchors.centerIn: parent; text: done.checked ? '✓' : ''; color: backend.colors.onAccent }
                }
                contentItem: Copy { leftPadding: 38; text: 'Свой проект написал, запустил и проверил по всем пунктам'; verticalAlignment: Text.AlignVCenter }
            }
            Copy { width: parent.width; text: 'Это твоя отметка самопроверки. Приложение проверяет ответы теста, но не запускает и не оценивает твой .py-файл.'; color: backend.colors.muted; font.pixelSize: 13 }
            AppButton {
                objectName: 'nextSection'
                text: page.checkpoint.key === 'practice' ? 'Завершить Python Core  →' : 'К следующему разделу  →'
                primary: true
                enabled: page.state.projectDone && page.state.testPassed
                onClicked: { let key = backend.nextSection(); page.shell.navigate(key ? 'section' : 'overview', key || 'Python Core') }
            }
        }
    }
}
