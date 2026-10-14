import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

ColumnLayout {
    id: settings
    property var appearance: backend.workspace.terminalAppearance
    property var colors: appearance.colors
    property string notice: ''
    spacing: 12
    function apply() {
        appearance.apply(fonts.currentText, size.value, ['dark', 'light', 'midnight', 'custom'][theme.currentIndex], background.text, foreground.text, cursor.text)
    }
    FileDialog {
        id: fontFile
        title: 'Выбери шрифт терминала'
        nameFilters: ['Шрифты (*.ttf *.otf)']
        onAccepted: appearance.importFont(selectedFile.toString())
    }
    Label { Layout.fillWidth: true; text: 'Шрифт'; color: settings.colors.foreground }
    ComboBox {
        id: fonts; objectName: 'terminalFont'
        Layout.fillWidth: true
        model: settings.appearance.fonts
        currentIndex: Math.max(0, model.indexOf(settings.appearance.fontFamily))
        Accessible.name: 'Шрифт терминала'
        onActivated: settings.apply()
    }
    Button { text: 'Добавить свой шрифт…'; onClicked: fontFile.open() }
    RowLayout {
        Layout.fillWidth: true
        Label { text: 'Размер'; color: settings.colors.foreground; Layout.fillWidth: true }
        SpinBox {
            id: size; objectName: 'terminalFontSize'
            from: 10; to: 32; value: settings.appearance.fontSize; editable: true
            Accessible.name: 'Размер шрифта терминала'
            onValueModified: settings.apply()
        }
    }
    Label { Layout.fillWidth: true; text: 'Тема терминала'; color: settings.colors.foreground }
    ComboBox {
        id: theme; objectName: 'terminalTheme'
        Layout.fillWidth: true
        model: ['Тёмная', 'Светлая', 'Ночная', 'Своя']
        currentIndex: ['dark', 'light', 'midnight', 'custom'].indexOf(settings.appearance.theme)
        Accessible.name: 'Тема терминала'
        onActivated: settings.apply()
    }
    Label { Layout.fillWidth: true; text: 'Свои цвета: #RRGGBB'; visible: theme.currentIndex === 3; color: settings.colors.muted }
    Label { text: 'Фон'; visible: theme.currentIndex === 3; color: settings.colors.foreground }
    TextField { id: background; objectName: 'terminalBackground'; Layout.fillWidth: true; visible: theme.currentIndex === 3; text: settings.appearance.customColors.background; selectByMouse: true; Accessible.name: 'Цвет фона терминала'; onAccepted: settings.apply() }
    Label { text: 'Текст'; visible: theme.currentIndex === 3; color: settings.colors.foreground }
    TextField { id: foreground; objectName: 'terminalForeground'; Layout.fillWidth: true; visible: theme.currentIndex === 3; text: settings.appearance.customColors.foreground; selectByMouse: true; Accessible.name: 'Цвет текста терминала'; onAccepted: settings.apply() }
    Label { text: 'Курсор'; visible: theme.currentIndex === 3; color: settings.colors.foreground }
    TextField { id: cursor; objectName: 'terminalCursor'; Layout.fillWidth: true; visible: theme.currentIndex === 3; text: settings.appearance.customColors.cursor; selectByMouse: true; Accessible.name: 'Цвет курсора терминала'; onAccepted: settings.apply() }
    Button { text: 'Применить цвета'; visible: theme.currentIndex === 3; onClicked: settings.apply() }
    Rectangle {
        Layout.fillWidth: true; implicitHeight: Math.max(100, preview.implicitHeight + 24)
        color: settings.colors.background; border.color: settings.colors.border; radius: 8
        Text {
            id: preview
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
            text: '>>> print("Привет!")\nПривет!\n▏'
            textFormat: Text.PlainText; wrapMode: Text.WrapAnywhere
            font.family: settings.appearance.fontFamily; font.pixelSize: settings.appearance.fontSize
            color: settings.colors.foreground
        }
    }
    Label { Layout.fillWidth: true; wrapMode: Text.WordWrap; text: settings.appearance.status || 'Изменения сохраняются отдельно от темы приложения.'; color: settings.colors.muted }
}
