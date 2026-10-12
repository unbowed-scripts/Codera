import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: landing
    required property var shell
    property bool running: false
    readonly property int availableCount: backend.languages.filter(function(language) { return language.available }).length
    clip: true
    // Keep the existing quiet background motion behind the scrollable catalog.
    Repeater {
        model: 20
        Item {
            id: stream
            required property int index
            x: index * landing.width / 20
            y: landing.height * .35
            width: 18; height: landing.height * .65; clip: true
            Text {
                id: digits
                text: '0\n1\n{\n0\np\n1\n}\n0\n1'
                color: backend.colors.accent; font.family: 'monospace'; font.pixelSize: 12
                opacity: .08
                NumberAnimation on y {
                    from: stream.height + (stream.index % 7) * 36; to: -digits.height
                    duration: 13000 + (stream.index % 6) * 1100
                    loops: Animation.Infinite
                    running: landing.running && !backend.reducedMotion
                }
            }
        }
    }
    LanguagePlan { id: languagePlan; shell: landing.shell }
    Flickable {
        id: catalog
        objectName: 'languageCatalog'
        anchors { fill: parent; margins: landing.width < 700 ? 20 : 32 }
        contentWidth: width; contentHeight: content.height + 32
        clip: true; boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: AppScrollBar {}
        FastScroll { scroller: catalog }
        Column {
            id: content
            width: Math.min(1120, catalog.width - 14)
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 24
            Item { width: 1; height: 8 }
            Copy { width: parent.width; text: 'УЧИСЬ ПИСАТЬ СВОИ ПРОГРАММЫ'; color: backend.colors.accent; font.pixelSize: 11 }
            Copy { width: parent.width; text: 'Выбери язык программирования'; font.pixelSize: landing.width < 700 ? 34 : 44; font.weight: Font.DemiBold }
            Copy { width: parent.width; text: 'Изучай Python или посмотри программы будущих курсов.'; font.pixelSize: 17; color: backend.colors.muted }
            GridLayout {
                width: parent.width
                columns: landing.width < 600 ? 1 : 3
                Copy { text: 'Каталог языков'; font.pixelSize: 23; font.weight: Font.DemiBold }
                Item { Layout.fillWidth: true }
                Copy { text: 'Доступно: ' + landing.availableCount + ' · В планах: ' + (backend.languages.length - landing.availableCount); font.pixelSize: 12; color: backend.colors.muted }
            }
            GridLayout {
                id: grid
                width: parent.width
                columns: width >= 1000 ? 3 : width >= 640 ? 2 : 1
                columnSpacing: 16; rowSpacing: 16
                Repeater {
                    model: backend.languages
                    Card {
                        id: languageCard
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredWidth: (grid.width - (grid.columns - 1) * grid.columnSpacing) / grid.columns
                        Layout.preferredHeight: Math.max(284, languageBody.implicitHeight + 40)
                        color: modelData.available ? backend.colors.feature : backend.colors.surface
                        border.color: modelData.available ? backend.colors.featureBorder : backend.colors.border
                        Column {
                            id: languageBody
                            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                            spacing: 14
                            RowLayout {
                                width: parent.width
                                LanguageAvatar { languageKey: languageCard.modelData.key }
                                Item { Layout.fillWidth: true }
                                Copy { text: languageCard.modelData.status; color: languageCard.modelData.available ? backend.colors.accent : backend.colors.muted; font.pixelSize: 12 }
                            }
                            Copy { width: parent.width; text: languageCard.modelData.name; font.pixelSize: 22; font.weight: Font.DemiBold }
                            Copy { width: parent.width; height: Math.max(48, implicitHeight); text: languageCard.modelData.description; color: backend.colors.muted; font.pixelSize: 14 }
                            AppButton {
                                objectName: languageCard.modelData.available ? 'startPython' : 'plan_' + languageCard.modelData.key
                                width: parent.width
                                text: languageCard.modelData.available ? 'Начать изучение  →' : 'Посмотреть программу  →'
                                primary: languageCard.modelData.available
                                onActiveFocusChanged: {
                                    if (activeFocus) {
                                        let top = languageCard.mapToItem(content, 0, 0).y
                                        if (top < catalog.contentY) catalog.contentY = top
                                        else if (top + languageCard.height > catalog.contentY + catalog.height)
                                            catalog.contentY = Math.min(catalog.contentHeight - catalog.height, top + languageCard.height - catalog.height)
                                    }
                                }
                                onClicked: {
                                    if (languageCard.modelData.available) landing.shell.enterCourse()
                                    else { languagePlan.language = languageCard.modelData; languagePlan.opener = this; languagePlan.open() }
                                }
                            }
                        }
                    }
                }
            }
            Card {
                width: parent.width; height: future.height + 40
                Column {
                    id: future
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
                    spacing: 12
                    Copy { width: parent.width; text: 'Другие направления'; font.pixelSize: 20; font.weight: Font.DemiBold }
                    Copy { width: parent.width; text: backend.futureLanguages.join(' · '); color: backend.colors.accent; font.pixelSize: 17 }
                    Copy { width: parent.width; text: 'В планах — курсы для мобильных приложений, системных программ и других задач.'; color: backend.colors.muted }
                }
            }
        }
    }
}
