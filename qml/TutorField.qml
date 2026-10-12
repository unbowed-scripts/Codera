import QtQuick
import QtQuick.Controls

TextField {
    height: 46
    selectByMouse: true
    color: backend.colors.text
    placeholderTextColor: backend.colors.muted
    font.pixelSize: 14
    Accessible.name: placeholderText
    background: Rectangle {
        radius: 10
        color: backend.colors.input
        border.width: parent.activeFocus ? 2 : 1
        border.color: parent.activeFocus ? backend.colors.accent : backend.colors.border
    }
}
