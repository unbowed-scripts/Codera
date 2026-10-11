import QtQuick
import QtQuick.Layouts

Column {
    id: page
    required property var shell
    spacing: 24
    Copy { width: parent.width; text: 'ТВОЙ ПУТЬ В ПРОГРАММИРОВАНИЕ'; font.pixelSize: 11; color: backend.colors.muted }
    Copy { objectName: 'pageTitle'; width: parent.width; text: backend.track; font.pixelSize: 32; font.weight: Font.DemiBold }
    Copy { width: parent.width; text: backend.track === 'Python Core' ? 'От первой строки кода — к самостоятельным программам.' : backend.track === 'Web' ? 'От запроса в браузере — к своему веб-приложению.' : 'От массива чисел — к осмысленному анализу данных.'; color: backend.colors.muted }
    Card {
        width: parent.width; height: feature.height + 48
        color: backend.colors.feature; border.color: backend.colors.featureBorder
        Column {
            id: feature
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 16
            Copy { width: parent.width; text: !backend.progress.ready ? 'НАПРАВЛЕНИЕ ГОТОВИТСЯ' : backend.progress.repeat ? 'МОЖНО ПОВТОРИТЬ' : 'СЛЕДУЮЩИЙ ШАГ'; font.pixelSize: 11; color: backend.colors.muted }
            Copy { width: parent.width; text: backend.progress.nextTitle; font.pixelSize: 24; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: backend.progress.ready ? backend.progress.readyDone + ' / ' + backend.progress.ready + ' доступных уроков пройдено' : 'Изучи программу разделов. Первые задания уже доступны в Python Core.'; color: backend.colors.muted }
            Copy { width: parent.width; visible: backend.progress.ready > 0; text: 'Самостоятельная практика: ' + backend.progress.practiced + ' / ' + backend.progress.ready + '. Отмечается тобой после запуска своего кода.'; color: backend.colors.muted; font.pixelSize: 13 }
            Copy { width: parent.width; visible: backend.track === 'Python Core'; text: 'Итоги разделов: тесты ' + backend.progress.sectionTests + ' / 9 · проекты ' + backend.progress.sectionProjects + ' / 9'; color: backend.colors.muted; font.pixelSize: 13 }
            Copy { width: parent.width; visible: backend.progress.webReady; text: 'Python Core завершён по твоим отметкам. Проверь итоговый проект и переходи к маршруту Web.'; color: backend.colors.codeText }
            AppButton {
                objectName: 'continueLearning'
                text: !backend.progress.ready ? 'Перейти в Python Core  →' : backend.progress.nextKind === 'checkpoint' ? 'Завершить раздел  →' : backend.progress.repeat ? 'Повторить урок  →' : backend.progress.readyDone ? 'Продолжить обучение  →' : 'Начать обучение  →'
                primary: true
                onClicked: page.shell.navigate(backend.progress.ready ? backend.progress.nextKind : 'overview', backend.progress.ready ? backend.progress.continueKey : 'Python Core')
            }
        }
    }
    Copy { width: parent.width; text: 'Разделы курса'; font.pixelSize: 23; font.weight: Font.DemiBold }
    Grid {
        width: parent.width
        columns: width >= 720 ? 2 : 1
        spacing: 16
        Repeater {
            model: backend.sections
            Card {
                required property var modelData
                required property int index
                width: (parent.width - (parent.columns - 1) * parent.spacing) / parent.columns
                height: Math.max(238, sectionBody.implicitHeight + 44)
                Column {
                    id: sectionBody
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 22 }
                    spacing: 14
                    RowLayout {
                        width: parent.width
                        Copy { text: ('0' + (index+1)).slice(-2); color: backend.colors.accent; font.pixelSize: 18 }
                        Item { Layout.fillWidth: true }
                        Copy { text: modelData.ready ? modelData.ready + ' доступны' : 'Готовится'; font.pixelSize: 12; color: backend.colors.muted }
                    }
                    Copy { width: parent.width; text: modelData.title; font.pixelSize: 18; font.weight: Font.DemiBold }
                    Copy { width: parent.width; height: Math.max(64, implicitHeight); text: modelData.outcome; font.pixelSize: 14; color: backend.colors.muted }
                    AppButton { text: modelData.count + ' уровней  →'; quiet: true; onClicked: page.shell.navigate('section', modelData.key) }
                }
            }
        }
    }
    Copy { width: parent.width; text: 'Уроки можно открывать свободно. Итоговый тест и мини-проект доступны после шести уровней раздела.'; font.pixelSize: 12; color: backend.colors.muted }
}
