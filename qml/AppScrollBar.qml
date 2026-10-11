import QtQuick
import QtQuick.Controls

ScrollBar {
    id: bar
    policy: ScrollBar.AsNeeded
    padding: 2
    implicitWidth: 10
    minimumSize: 0.06
    contentItem: Rectangle {
        implicitWidth: 6
        radius: 3
        color: bar.pressed ? backend.colors.accent : backend.colors.muted
        opacity: bar.active || bar.hovered ? 0.85 : 0.35
    }
    background: Rectangle { color: 'transparent' }
}
