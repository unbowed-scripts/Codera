import QtQuick
import QtQuick.Layouts

Column {
    id: page
    required property var shell
    spacing: 20
    AppButton { text: '←  Все разделы'; quiet: true; onClicked: page.shell.navigate('overview', backend.track) }
    Copy { objectName: 'pageTitle'; width: parent.width; text: backend.page.title; font.pixelSize: 32; font.weight: Font.DemiBold }
    Copy { width: parent.width; text: backend.page.outcome; color: backend.colors.muted }
    Repeater {
        model: backend.page.levels || []
        Card {
            required property var modelData
            width: parent.width; height: Math.max(98, row.implicitHeight + 32)
            GridLayout {
                id: row
                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 20 }
                columns: page.width < 500 ? 2 : 3
                rowSpacing: 16; columnSpacing: 16
                Copy { text: ('0' + modelData.index).slice(-2); color: backend.colors.accent; font.pixelSize: 20 }
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 8
                    Copy { Layout.fillWidth: true; text: modelData.title; font.pixelSize: 17; font.weight: Font.DemiBold }
                    Copy { Layout.fillWidth: true; text: modelData.status; color: backend.colors.muted; font.pixelSize: 12 }
                }
                AppButton { text: 'Открыть  →'; quiet: !modelData.available; onClicked: page.shell.navigate('lesson', modelData.key) }
            }
        }
    }
    Card {
        width: parent.width
        visible: backend.page.checkpoint === true
        height: visible ? checkpointContent.height + 40 : 0
        color: backend.colors.feature
        Column {
            id: checkpointContent
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
            spacing: 14
            Copy { width: parent.width; text: 'После ' + (backend.page.levelCount || backend.page.count) + ' уровней'; font.pixelSize: 20; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: backend.page.testPassed && backend.page.projectDone ? 'Тест пройден, мини-проект выполнен. Можно повторить.' : 'Итоговый тест, разбор кода и свой мини-проект с подсказками и готовым примером.' }
            Copy { width: parent.width; text: 'Уроки: ' + (backend.page.levelsDone || 0) + ' / ' + (backend.page.levelCount || backend.page.count) + '. Тест: ' + (backend.page.testPassed ? 'пройден' : 'впереди') + '. Проект: ' + (backend.page.projectDone ? 'выполнен' : 'впереди') + '.'; color: backend.colors.muted }
            AppButton { objectName: 'openCheckpoint'; width: Math.min(implicitWidth, parent.width); text: backend.page.unlocked ? 'Тест и мини-проект  →' : 'Что будет после раздела  →'; onClicked: page.shell.navigate('checkpoint', backend.page.key) }
        }
    }
}
