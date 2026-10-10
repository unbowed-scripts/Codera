import QtQuick
import QtQuick.Controls

Button {
    id: control
    property bool primary: false
    property bool quiet: false
    property bool selected: false
    implicitHeight: 44
    implicitWidth: Math.max(88, contentItem.implicitWidth + 32)
    padding: 12
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text
    contentItem: Text {
        text: control.text
        color: !control.enabled ? '#839388' : control.primary ? '#142a1b' : control.selected ? '#a6efbd' : '#edf2ee'
        font.pixelSize: 14
        font.weight: control.primary ? Font.DemiBold : Font.Medium
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: 12
        color: !control.enabled ? '#1a201c' : control.down ? '#4b7058' : control.primary ? (control.hovered ? '#c0f8d2' : '#a6efbd') : control.selected ? '#243c2c' : control.hovered ? '#2b352e' : control.quiet ? 'transparent' : '#202722'
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? '#c4f7d4' : control.primary ? 'transparent' : control.quiet ? 'transparent' : '#354039'
        Behavior on color { ColorAnimation { duration: backend.reducedMotion ? 0 : 100 } }
    }
}
