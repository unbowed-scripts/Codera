import QtQuick
import QtQuick.Layouts

Column {
    id: page
    required property var shell
    spacing: 20
    AppButton { text: '←  Все разделы'; quiet: true; onClicked: page.shell.navigate('overview', backend.track) }
    Copy { objectName: 'pageTitle'; width: parent.width; text: 'Твой маршрут обучения'; font.pixelSize: 32; font.weight: Font.DemiBold }
    Copy { width: parent.width; text: 'Одна тема — одно небольшое восхождение.'; color: backend.colors.muted }
    Mountain { width: parent.width }
    Repeater {
        model: backend.route
        Card {
            required property var modelData
            required property int index
            width: parent.width; height: row.implicitHeight + 40
            RowLayout {
                id: row
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                spacing: 20
                Copy { text: ('0' + (index+1)).slice(-2); color: backend.colors.accent; font.pixelSize: 22 }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 8
                    Copy { Layout.fillWidth: true; text: modelData.title; font.pixelSize: 18; font.weight: Font.DemiBold }
                    Copy { Layout.fillWidth: true; text: modelData.description; color: backend.colors.muted }
                }
            }
        }
    }
}
