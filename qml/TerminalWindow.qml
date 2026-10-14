import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: terminalWindow
    objectName: 'terminalWindow'
    width: 1120; height: 760
    minimumWidth: 320; minimumHeight: 360
    visible: false
    transientParent: null
    flags: Qt.Window
    modality: Qt.NonModal
    font.pixelSize: 14
    title: 'Терминал · ' + ws.title + ' — PythonTech'
    property var ws: backend.workspace
    property var colors: ws.terminalAppearance.colors
    property bool narrow: width < 800
    property bool tasksVisible: !narrow
    color: colors.background
    palette.window: colors.surface
    palette.windowText: colors.foreground
    palette.text: colors.foreground
    palette.base: colors.background
    palette.button: colors.surface
    palette.buttonText: colors.foreground
    palette.highlight: colors.selection
    palette.highlightedText: colors.foreground
    function revealTerminal() {
        if (visibility === Window.Minimized) showNormal()
        else show()
        if (ws.windowActivationSupported) raise()
        requestActivate()
        focusTimer.restart()
    }
    Timer { id: focusTimer; interval: 80; onTriggered: terminal.forceActiveFocus() }
    onVisibleChanged: ws.terminalWindowVisible(visible)
    onClosing: ws.closeTerminal()
    Connections {
        target: terminalWindow.ws
        function onTerminalRequested() { terminalWindow.revealTerminal() }
        function onTerminalWindowChanged() { if (!terminalWindow.ws.terminalWindowOpen) terminalWindow.hide() }
    }
    header: Rectangle {
        color: terminalWindow.colors.surface
        implicitHeight: tools.implicitHeight + 24
        ColumnLayout {
            id: tools
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                Label { Layout.fillWidth: true; text: 'Терминал'; font.pixelSize: 20; font.bold: true; color: terminalWindow.colors.foreground }
                Button { objectName: 'terminalTasks'; text: 'Задачи'; checkable: true; checked: terminalWindow.tasksVisible; onClicked: terminalWindow.tasksVisible = checked }
                Button { objectName: 'terminalAppearanceButton'; text: 'Оформление'; onClicked: appearance.open() }
            }
            Flow {
                Layout.fillWidth: true; spacing: 8
                Button { objectName: 'terminalRestart'; text: 'Новый сеанс'; enabled: !terminalWindow.ws.terminal.running && !terminalWindow.ws.runtime.busy; onClicked: terminalWindow.ws.startTerminal() }
                Button { objectName: 'terminalInterrupt'; text: 'Ctrl+C'; enabled: terminalWindow.ws.terminal.running; onClicked: { terminalWindow.ws.terminal.interrupt(); terminal.forceActiveFocus() } }
                Button { text: 'Вставить'; enabled: terminalWindow.ws.terminal.running; onClicked: terminal.paste() }
                Button { text: 'Копировать'; onClicked: terminal.copySelection() }
            }
        }
    }
    Drawer {
        id: appearance
        objectName: 'terminalAppearanceDrawer'
        edge: Qt.RightEdge
        width: Math.min(380, terminalWindow.width)
        height: terminalWindow.height
        padding: 20
        background: Rectangle { color: terminalWindow.colors.surface; border.color: terminalWindow.colors.border }
        contentItem: ScrollView {
            contentWidth: availableWidth; clip: true
            ColumnLayout {
                width: parent.width
                spacing: 16
                RowLayout {
                    Layout.fillWidth: true
                    Label { text: 'Оформление'; font.pixelSize: 22; Layout.fillWidth: true; color: terminalWindow.colors.foreground }
                    Button { text: 'Закрыть'; onClicked: appearance.close() }
                }
                TerminalAppearance { Layout.fillWidth: true }
            }
        }
        onClosed: terminal.forceActiveFocus()
    }
    RowLayout {
        anchors.fill: parent
        spacing: 0
        Rectangle {
            visible: terminalWindow.tasksVisible
            Layout.preferredWidth: terminalWindow.narrow ? terminalWindow.width : 292
            Layout.fillHeight: true
            color: terminalWindow.colors.surface
            ScrollView {
                anchors.fill: parent; anchors.margins: 16
                contentWidth: availableWidth; clip: true
                ColumnLayout {
                    width: parent.width
                    spacing: 16
                    Label { Layout.fillWidth: true; text: terminalWindow.ws.title; wrapMode: Text.WordWrap; font.bold: true; font.pixelSize: 18; color: terminalWindow.colors.foreground }
                    Label { Layout.fillWidth: true; text: terminalWindow.ws.task; wrapMode: Text.WordWrap; color: terminalWindow.colors.foreground }
                    Repeater {
                        model: terminalWindow.ws.tasks
                        CheckBox {
                            id: task
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true
                            text: modelData.text; checked: modelData.done
                            implicitHeight: Math.max(40, contentItem.implicitHeight + 12)
                            contentItem: Label { leftPadding: 34; text: task.text; wrapMode: Text.WordWrap; color: terminalWindow.colors.foreground }
                            onToggled: terminalWindow.ws.checkTask(index, checked)
                        }
                    }
                    Button { objectName: 'terminalComplete'; text: 'Готово →'; enabled: !terminalWindow.ws.runtime.busy; onClicked: terminalWindow.ws.complete() }
                    Label { Layout.fillWidth: true; text: 'Отметь критерии после своей проверки. Код автоматически не оценивается.'; wrapMode: Text.WordWrap; color: terminalWindow.colors.muted }
                }
            }
        }
        TerminalView {
            id: terminal
            visible: !terminalWindow.narrow || !terminalWindow.tasksVisible
            Layout.fillWidth: true; Layout.fillHeight: true
        }
    }
    footer: Rectangle {
        color: terminalWindow.colors.surface
        implicitHeight: status.implicitHeight + 16
        ColumnLayout {
            id: status
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 8 }
            spacing: 4
            Label {
                Layout.fillWidth: true
                text: terminalWindow.ws.terminal.running ? 'Сеанс работает · Ctrl+Shift+C / V — копировать / вставить' : 'Сеанс завершён · Нажми «Новый сеанс», чтобы продолжить'
                wrapMode: Text.WordWrap; color: terminalWindow.colors.muted; font.pixelSize: 12
            }
            Label { Layout.fillWidth: true; text: terminalWindow.ws.project; elide: Text.ElideMiddle; color: terminalWindow.colors.muted; font.pixelSize: 11 }
        }
    }
}
