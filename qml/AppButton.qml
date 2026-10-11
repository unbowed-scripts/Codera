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
        color: !control.enabled ? backend.colors.disabledText : control.primary ? backend.colors.onAccent : control.selected ? backend.colors.accent : backend.colors.text
        font.pixelSize: 14
        font.weight: control.primary ? Font.DemiBold : Font.Medium
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: 12
        color: !control.enabled ? backend.colors.disabled : control.primary ? (control.hovered || control.down ? backend.colors.accentHover : backend.colors.accent) : control.down ? backend.colors.pressed : control.selected ? backend.colors.selected : control.hovered ? backend.colors.hover : control.quiet ? 'transparent' : backend.colors.button
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? backend.colors.accent : control.primary ? 'transparent' : control.quiet ? 'transparent' : backend.colors.border
        Behavior on color { ColorAnimation { duration: backend.reducedMotion ? 0 : 100 } }
    }
}
