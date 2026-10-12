import QtQuick
import QtQuick.Controls

Column {
    id: panel
    required property string target
    property bool expanded: false
    property bool restoring: false
    property var result: ({text: '', error: ''})
    width: parent.width
    spacing: 12
    function refresh() { result = backend.tutor.state(target) }
    function restore() {
        restoring = true
        const draft = backend.tutorDraft(target)
        code.text = draft.code
        question.text = draft.question
        refresh()
        restoring = false
    }
    Component.onCompleted: restore()
    Connections {
        target: backend
        function onPageChanged() { panel.expanded = false; panel.restore() }
    }
    Connections {
        target: backend.tutor
        function onChanged() { panel.refresh() }
    }
    AppButton {
        objectName: 'tutorToggle_' + panel.target
        text: panel.expanded ? 'Скрыть ИИ-помощника' : 'Помощь ИИ'
        onClicked: panel.expanded = !panel.expanded
    }
    Column {
        visible: panel.expanded
        width: parent.width
        spacing: 12
        Copy { width: parent.width; text: backend.tutor.connected ? 'ИИ получит задание и твой текущий ответ. Добавь код или уточни вопрос.' : 'Подключи свою модель в настройках → ИИ-помощник.'; color: backend.colors.muted }
        Copy { width: parent.width; text: 'Твой код (необязательно)'; font.weight: Font.DemiBold }
        TextArea {
            id: code
            objectName: 'tutorCode_' + panel.target
            width: parent.width
            height: Math.max(140, implicitHeight)
            placeholderText: 'Вставь код из своего .py-файла'
            textFormat: TextEdit.PlainText
            wrapMode: TextEdit.Wrap
            selectByMouse: true
            color: backend.colors.text
            placeholderTextColor: backend.colors.muted
            font.family: 'monospace'
            font.pixelSize: 14
            Accessible.name: 'Код для ИИ-помощника'
            onTextChanged: if (!panel.restoring) backend.saveTutorDraft(panel.target, text, question.text)
            background: Rectangle { color: backend.colors.input; radius: 10; border.color: code.activeFocus ? backend.colors.accent : backend.colors.border }
        }
        TutorField {
            id: question
            objectName: 'tutorQuestion_' + panel.target
            width: parent.width
            placeholderText: 'Твой вопрос'
            onTextEdited: backend.saveTutorDraft(panel.target, code.text, text)
        }
        Copy { width: parent.width; text: 'По кнопке «Получить подсказку» выбранный провайдер получит задание, пример, твой ответ, вставленный код и вопрос. ИИ не читает файлы с компьютера.'; font.pixelSize: 12; color: backend.colors.muted }
        Flow {
            width: parent.width
            spacing: 8
            AppButton {
                objectName: 'tutorAsk_' + panel.target
                text: backend.tutor.busy ? 'Ожидаем ответ…' : 'Получить подсказку'
                primary: true
                enabled: backend.tutor.connected && !backend.tutor.busy
                onClicked: backend.tutor.ask(panel.target, code.text, question.text)
            }
            AppButton { visible: backend.tutor.busy; text: 'Отменить'; onClicked: backend.tutor.cancel() }
        }
        Copy { width: parent.width; visible: text.length > 0; text: panel.result.error; color: backend.colors.warning }
        Repeater {
            model: panel.result.text ? panel.result.text.split('```') : []
            Column {
                required property string modelData
                required property int index
                width: parent.width
                visible: modelData.trim().length > 0
                Copy { visible: index % 2 === 0; width: parent.width; text: modelData }
                CodeHint { visible: index % 2 === 1; code: modelData.replace(/^python\s*\n/, '').trim() }
            }
        }
        Copy { visible: panel.result.text.length > 0; width: parent.width; text: 'Проверь совет ИИ: запусти код и сравни результат с критериями.'; font.pixelSize: 12; color: backend.colors.muted }
    }
}
