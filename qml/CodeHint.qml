import QtQuick
import QtQuick.Controls

Card {
    id: block
    property string code: ''
    width: parent.width
    height: content.height + 32
    color: backend.colors.code
    Column {
        id: content
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
        spacing: 10
        Copy { width: parent.width; text: 'ПРИМЕР КОДА'; font.pixelSize: 11; color: backend.colors.muted }
        TextEdit {
            width: parent.width
            text: block.code
            textFormat: TextEdit.PlainText
            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            color: backend.colors.codeText
            font.family: 'monospace'
            font.pixelSize: 14
            Accessible.name: 'Пример кода'
        }
    }
}
