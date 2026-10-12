import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: plan
    objectName: 'languagePlan'
    required property var shell
    property var language: ({key:'python', name:'', goal:'', modules:[], finalProject:'', available:false})
    property var opener: null
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(780, parent.width - 40)
    height: Math.min(830, parent.height - 40)
    padding: width < 500 ? 12 : 24
    modal: true; focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    onOpened: { scroll.contentY = 0; closeButton.forceActiveFocus() }
    onClosed: if (opener) opener.forceActiveFocus()
    background: Rectangle { radius: 20; color: backend.colors.background; border.color: backend.colors.border }
    Overlay.modal: Rectangle { color: backend.colors.overlay }
    contentItem: ColumnLayout {
        spacing: 20
        GridLayout {
            columns: plan.width < 500 ? 2 : 3
            rowSpacing: 16; columnSpacing: 16
            Layout.fillWidth: true
            LanguageAvatar { languageKey: plan.language.key }
            ColumnLayout {
                Layout.fillWidth: true; spacing: 4
                Copy { Layout.fillWidth: true; text: plan.language.name; font.pixelSize: 26; font.weight: Font.DemiBold }
                Copy { Layout.fillWidth: true; text: plan.language.available ? 'Курс доступен' : 'Программа будущего курса'; color: backend.colors.muted; font.pixelSize: 13 }
            }
            AppButton { id: closeButton; objectName: 'closeLanguagePlan'; text: 'Закрыть'; quiet: true; onClicked: plan.close() }
        }
        Flickable {
            id: scroll
            objectName: 'languagePlanScroll'
            Layout.fillWidth: true; Layout.fillHeight: true
            contentWidth: width; contentHeight: content.height
            clip: true; boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: AppScrollBar {}
            FastScroll { scroller: scroll }
            Column {
                id: content
                width: parent.width - 14; spacing: 20
                Copy { width: parent.width; text: plan.language.goal; font.pixelSize: 16 }
                Copy { width: parent.width; visible: !plan.language.available; text: 'Уроки ещё готовятся. Ниже — темы и итоговый проект. Дата запуска пока не назначена.'; color: backend.colors.muted }
                Copy { width: parent.width; text: plan.language.available ? 'Core: 54 урока · Web: 42 урока' : '6 разделов · по 6 уроков'; color: backend.colors.accent; font.weight: Font.DemiBold }
                Copy { width: parent.width; text: 'Как будем учиться'; font.pixelSize: 20; font.weight: Font.DemiBold }
                Copy { width: parent.width; text: 'В уроке: теория, пример и практика. После раздела: тест и мини-проект с подсказками.'; color: backend.colors.muted }
                Repeater {
                    model: plan.language.modules
                    Card {
                        required property var modelData
                        required property int index
                        width: parent.width; height: moduleBody.height + 32
                        Column {
                            id: moduleBody
                            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 16 }
                            spacing: 8
                            Copy { width: parent.width; text: (index + 1) + '. ' + modelData.title; font.pixelSize: 17; font.weight: Font.DemiBold }
                            Copy { width: parent.width; text: modelData.topics; color: backend.colors.muted }
                        }
                    }
                }
                Copy { width: parent.width; text: 'Итоговый проект'; font.pixelSize: 20; font.weight: Font.DemiBold }
                Copy { width: parent.width; text: plan.language.finalProject }
            }
        }
        AppButton { visible: plan.language.available; text: 'Перейти к обучению  →'; primary: true; onClicked: { plan.close(); plan.shell.enterCourse() } }
    }
}
