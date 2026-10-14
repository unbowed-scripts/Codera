import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: workspace
    objectName: 'workspaceView'
    parent: Overlay.overlay
    x: 0; y: 0; width: parent.width; height: parent.height
    padding: width < 600 ? 10 : 18
    modal: !ws.terminalWindowOpen; focus: true
    closePolicy: Popup.NoAutoClose
    property var ws: backend.workspace
    property bool narrow: width < 800
    property bool showTasks: !narrow
    property bool setup: false
    property bool launchFile: false
    function launch(runFile) {
        launchFile = runFile
        ws.requestLaunch(runFile)
    }
    background: Rectangle { color: backend.colors.background }
    Connections {
        target: workspace.ws
        function onSetupRequested() { pythonSetup.open() }
        function onChanged() {
            if (workspace.ws.active && !workspace.opened) workspace.open()
            else if (!workspace.ws.active && workspace.opened) workspace.close()
        }
    }
    Shortcut { sequence: 'Ctrl+S'; enabled: workspace.opened; onActivated: workspace.ws.save() }
    Dialog {
        id: reloadDialog
        anchors.centerIn: parent; width: Math.min(440, workspace.width - 24)
        height: 210
        title: 'Перечитать файл?'
        modal: true; standardButtons: Dialog.Ok | Dialog.Cancel
        contentItem: Copy { text: 'Несохранённый текст редактора будет заменён содержимым файла с диска. Сначала скопируй нужные изменения.' }
        onAccepted: workspace.ws.reloadFile()
    }
    Dialog {
        id: pythonSetup
        objectName: 'pythonSetupDialog'
        anchors.centerIn: parent
        width: Math.min(500, workspace.width - 24)
        title: 'Python для терминала'
        modal: true
        standardButtons: Dialog.Cancel
        contentItem: ColumnLayout {
            spacing: 12
            Copy { Layout.fillWidth: true; text: 'Установим Python в папку PythonTech и создадим окружение проекта — отдельный Python с нужными пакетами. Терминал будет использовать его автоматически. Нужен интернет.' }
            Copy { Layout.fillWidth: true; text: 'В окружение установится pip для добавления пакетов. Для курса Web также нужны Flask и requests.'; color: backend.colors.muted }
            AppButton {
                objectName: 'installTerminalPython'
                Layout.fillWidth: true
                text: 'Установить и продолжить'
                primary: true
                onClicked: { pythonSetup.close(); workspace.setup = true; workspace.ws.setupAndLaunch(true, workspace.launchFile) }
            }
            AppButton {
                objectName: 'useTerminalPython'
                Layout.fillWidth: true
                visible: workspace.ws.runtime.python.length > 0
                text: 'Использовать выбранный Python'
                onClicked: { pythonSetup.close(); workspace.setup = true; workspace.ws.setupAndLaunch(false, workspace.launchFile) }
            }
            AppButton { Layout.fillWidth: true; text: 'Выбрать другой Python'; onClicked: { pythonSetup.close(); workspace.setup = true } }
        }
    }
    Menu {
        id: actions
        MenuItem { text: 'Открыть папку'; onTriggered: workspace.ws.openFolder() }
        MenuItem { text: 'Создать файл'; onTriggered: fileDialog.open() }
        MenuItem { text: 'Обновить список файлов'; onTriggered: workspace.ws.refreshFiles() }
        MenuItem { text: 'Перечитать файл'; onTriggered: reloadDialog.open() }
        MenuItem { text: 'Вставить в терминал'; onTriggered: workspace.ws.terminal.paste() }
    }
    Dialog {
        id: fileDialog
        anchors.centerIn: parent; width: Math.min(440, workspace.width - 24); height: 180
        title: 'Новый файл'; modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        contentItem: TutorField { id: fileName; placeholderText: 'main.py' }
        onAccepted: if (workspace.ws.createFile(fileName.text)) fileName.clear()
    }
    contentItem: ColumnLayout {
        spacing: 8
        Flow {
            Layout.fillWidth: true; spacing: 8
            AppButton { text: workspace.narrow ? '← Урок' : '← К уроку'; onClicked: workspace.ws.close() }
            AppButton { text: workspace.showTasks ? 'К работе' : 'Задачи'; onClicked: { workspace.showTasks = !workspace.showTasks; workspace.setup = false } }
            AppButton { objectName: 'openTerminal'; text: workspace.ws.terminalWindowOpen ? 'Показать терминал' : 'Открыть терминал'; enabled: !workspace.ws.runtime.busy; onClicked: workspace.launch(false) }
            AppButton { text: workspace.setup ? 'К коду' : 'Python'; onClicked: workspace.setup = !workspace.setup }
        }
        Copy { Layout.fillWidth: true; text: workspace.ws.title; font.pixelSize: 19; font.weight: Font.DemiBold }
        Copy { Layout.fillWidth: true; text: workspace.ws.project; font.pixelSize: 11; color: backend.colors.muted; maximumLineCount: 2; wrapMode: Text.WrapAnywhere }
        ScrollView {
            id: setupScroll
            visible: workspace.setup
            Layout.fillWidth: true; Layout.fillHeight: true; clip: true
            contentWidth: availableWidth
            WorkspaceSettings {
                id: setupSettings
                width: setupScroll.availableWidth
                reveal: function(item) {
                    const y = item.mapToItem(setupSettings, 0, 0).y
                    const scroll = setupScroll.contentItem
                    if (y < scroll.contentY) scroll.contentY = y
                    else if (y + item.height > scroll.contentY + setupScroll.height)
                        scroll.contentY = Math.max(0, y + item.height - setupScroll.height)
                }
            }
        }
        GridLayout {
            visible: !workspace.setup
            Layout.fillWidth: true; Layout.fillHeight: true
            columns: workspace.narrow ? 1 : 2
            columnSpacing: 16; rowSpacing: 8
            ScrollView {
                objectName: 'workspaceTasks'
                visible: workspace.showTasks
                Layout.preferredWidth: workspace.narrow ? -1 : 280
                Layout.fillWidth: workspace.narrow
                Layout.fillHeight: true
                contentWidth: availableWidth
                clip: true
                Column {
                    width: parent.width; spacing: 12
                    Copy { width: parent.width; text: 'Задача'; font.pixelSize: 18; font.weight: Font.DemiBold }
                    Copy { width: parent.width; text: workspace.ws.task }
                    Copy { width: parent.width; text: 'Проверь и отметь самостоятельно'; color: backend.colors.muted }
                    Repeater {
                        model: workspace.ws.tasks
                        CheckBox {
                            id: taskCheck
                            required property var modelData
                            required property int index
                            width: parent.width
                            text: modelData.text
                            checked: modelData.done
                            implicitHeight: Math.max(40, contentItem.implicitHeight + 12)
                            onToggled: workspace.ws.checkTask(index, checked)
                            contentItem: Copy { leftPadding: 32; text: taskCheck.modelData.text }
                        }
                    }
                    AppButton { objectName: 'workspaceComplete'; width: Math.min(implicitWidth, parent.width); text: 'Готово →'; primary: true; enabled: !workspace.ws.runtime.busy; onClicked: workspace.ws.complete() }
                    Copy { width: parent.width; text: 'Отметка завершает практику и открывает следующий урок. Ответы на вопросы проверяются отдельно.'; color: backend.colors.muted; font.pixelSize: 12 }
                }
            }
            ColumnLayout {
                visible: !workspace.narrow || !workspace.showTasks
                Layout.fillWidth: true; Layout.fillHeight: true
                spacing: 8
                Flow {
                    Layout.fillWidth: true; spacing: 6
                    AppButton { visible: workspace.narrow; text: 'Действия'; onClicked: actions.open() }
                    AppButton { visible: !workspace.narrow; text: 'Папка'; onClicked: workspace.ws.openFolder() }
                }
                Rectangle {
                    objectName: 'terminalNotice'
                    visible: workspace.ws.terminalWindowOpen
                    Layout.fillWidth: true
                    implicitHeight: notice.implicitHeight + 24
                    color: backend.colors.feature; radius: 8
                    ColumnLayout {
                        id: notice
                        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
                        Copy { Layout.fillWidth: true; text: 'Терминал открыт в новом окне'; font.weight: Font.DemiBold }
                        Copy { Layout.fillWidth: true; text: 'Переключись в окно терминала или нажми «Показать терминал». Здесь можно продолжать редактировать файлы.'; color: backend.colors.muted; font.pixelSize: 12 }
                    }
                }
                Copy { Layout.fillWidth: true; text: workspace.ws.runtime.status; font.pixelSize: 12; color: backend.colors.muted }
                Flow {
                    Layout.fillWidth: true; spacing: 6
                    ComboBox { id: files; objectName: 'workspaceFiles'; width: Math.min(240, parent.width); model: workspace.ws.files; currentIndex: workspace.ws.files.indexOf(workspace.ws.filename); onActivated: workspace.ws.selectFile(currentText) }
                    AppButton { visible: !workspace.narrow; text: 'Обновить'; onClicked: workspace.ws.refreshFiles() }
                    TutorField { visible: !workspace.narrow; id: newFile; width: Math.min(180, parent.width); placeholderText: 'Имя нового файла' }
                    AppButton { visible: !workspace.narrow; text: 'Создать файл'; onClicked: { if (workspace.ws.createFile(newFile.text)) newFile.clear() } }
                }
                Flow {
                    Layout.fillWidth: true; spacing: 6
                    AppButton { text: 'Сохранить'; onClicked: workspace.ws.save() }
                    AppButton { visible: !workspace.narrow; text: 'Перечитать файл'; onClicked: reloadDialog.open() }
                    AppButton { text: 'Запустить файл'; primary: true; enabled: !workspace.ws.runtime.busy; onClicked: workspace.launch(true) }
                    Copy { visible: !workspace.narrow; text: workspace.ws.filename + (workspace.ws.dirty ? ' •' : '') }
                }
                ScrollView {
                    Layout.fillWidth: true; Layout.fillHeight: true; Layout.preferredHeight: 240
                    clip: true
                    TextArea {
                        id: editor
                        objectName: 'workspaceEditor'
                        text: workspace.ws.content
                        color: backend.colors.codeText
                        font.family: 'monospace'; font.pixelSize: 14
                        selectByMouse: true; wrapMode: TextEdit.NoWrap
                        textFormat: TextEdit.PlainText
                        Accessible.name: 'Редактор файла'
                        onTextChanged: if (activeFocus) workspace.ws.content = text
                        Keys.onTabPressed: function(event) { insert(cursorPosition, '    '); event.accepted = true }
                        background: Rectangle { color: backend.colors.code; border.color: editor.activeFocus ? backend.colors.accent : backend.colors.border; radius: 8 }
                    }
                }

            }
        }
        Copy { objectName: 'workspaceStatus'; Layout.fillWidth: true; text: workspace.ws.status; color: backend.colors.muted; font.pixelSize: 12 }
    }
}
