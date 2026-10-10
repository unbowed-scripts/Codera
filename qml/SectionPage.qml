import QtQuick
import QtQuick.Layouts

Column {
    id: page
    required property var shell
    spacing: 20
    AppButton { text: '←  Все разделы'; quiet: true; onClicked: page.shell.navigate('overview', backend.track) }
    Copy { objectName: 'pageTitle'; width: parent.width; text: backend.page.title; font.pixelSize: 32; font.weight: Font.DemiBold }
    Copy { width: parent.width; text: backend.page.outcome; color: '#adb9b0' }
    Repeater {
        model: backend.page.levels || []
        Card {
            required property var modelData
            width: parent.width; height: Math.max(98, row.implicitHeight + 32)
            RowLayout {
                id: row
                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 20 }
                spacing: 16
                Copy { text: ('0' + modelData.index).slice(-2); color: '#a6efbd'; font.pixelSize: 20 }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 8
                    Copy { Layout.fillWidth: true; text: modelData.title; font.pixelSize: 17; font.weight: Font.DemiBold }
                    Copy { Layout.fillWidth: true; text: modelData.status; color: '#adb9b0'; font.pixelSize: 12 }
                }
                AppButton { text: 'Открыть  →'; quiet: !modelData.available; onClicked: page.shell.navigate('lesson', modelData.key) }
            }
        }
    }
}
