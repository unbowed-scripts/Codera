import QtQuick
import QtQuick.Controls

ComboBox {
    id: control
    implicitHeight: 44
    implicitWidth: 154
    leftPadding: 12
    rightPadding: 34
    hoverEnabled: true
    // Avoid the platform's white native popup in a dark theme.
    popup: Popup {
        objectName: control.objectName + 'Popup'
        y: control.height + 6
        width: control.width
        padding: 6
        implicitHeight: contentItem.implicitHeight + topPadding + bottomPadding
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        background: Rectangle {
            color: backend.colors.surface
            border.color: backend.colors.border
            radius: 12
        }
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
        }
    }
    delegate: ItemDelegate {
        id: option
        required property int index
        required property var modelData
        width: control.width - 12
        height: 40
        highlighted: control.highlightedIndex === index
        hoverEnabled: true
        contentItem: Text {
            text: option.modelData
            color: option.index === control.currentIndex ? backend.colors.accent : backend.colors.text
            font.pixelSize: 14
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        background: Rectangle {
            radius: 7
            color: option.highlighted || option.hovered ? backend.colors.selected : 'transparent'
        }
    }
    indicator: Text {
        x: control.width - width - 12
        y: (control.height - height) / 2
        text: control.popup.visible ? '⌃' : '⌄'
        color: backend.colors.muted
        font.pixelSize: 18
    }
    background: Rectangle {
        color: control.hovered ? backend.colors.hover : backend.colors.input
        border.color: control.activeFocus ? backend.colors.accent : backend.colors.border
        border.width: control.activeFocus ? 2 : 1
        radius: 10
    }
    contentItem: Text {
        text: control.displayText
        color: backend.colors.text
        font.pixelSize: 14
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    // Wheel scrolling a page must not accidentally change the chosen track/theme.
    wheelEnabled: false
}
