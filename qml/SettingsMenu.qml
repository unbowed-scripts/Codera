import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: settings
    objectName: 'settingsMenu'
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(940, parent.width - 40)
    height: Math.min(840, parent.height - 40)
    padding: width < 500 ? 12 : 24
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    onOpened: closeButton.forceActiveFocus()
    onClosed: opener.forceActiveFocus()
    required property var opener
    function closeInfo() {
        if (!info.opened) return false
        info.close()
        return true
    }
    function reveal(item) {
        const top = item.mapToItem(options, 0, 0).y
        if (top < scroll.contentY) scroll.contentY = top
        else if (top + item.height > scroll.contentY + scroll.height)
            scroll.contentY = Math.min(Math.max(0, scroll.contentHeight - scroll.height), top + item.height - scroll.height)
    }
    ReleaseInfo { id: info }
    background: Rectangle {
        color: backend.colors.background
        radius: 20
        border.color: backend.colors.border
    }
    Overlay.modal: Rectangle { color: backend.colors.overlay }
    contentItem: ColumnLayout {
        spacing: 20
        GridLayout {
            Layout.fillWidth: true
            columns: settings.width < 500 ? 1 : 2
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                Copy { text: 'Настройки'; font.pixelSize: 28; font.weight: Font.DemiBold }
                Copy { Layout.fillWidth: true; text: 'Язык, оформление и информация о PythonTech.'; color: backend.colors.muted; font.pixelSize: 14 }
            }
            AppButton { id: closeButton; objectName: 'closeSettings'; text: 'Закрыть'; quiet: true; onClicked: settings.close() }
        }
        Flickable {
            id: scroll
            objectName: 'settingsScroll'
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: options.height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: AppScrollBar {}
            FastScroll { scroller: scroll }
            Column {
                id: options
                width: scroll.width - 14
                spacing: 20
                Copy { text: 'Язык интерфейса'; font.pixelSize: 20; font.weight: Font.DemiBold }
                Copy { width: parent.width; text: 'Сейчас доступен русский. Английский и украинский появятся в будущих обновлениях.'; color: backend.colors.muted; font.pixelSize: 14 }
                Column {
                    width: parent.width
                    spacing: 8
                    Repeater {
                        model: [
                            { code: 'ru', label: 'Русский', available: true },
                            { code: 'en', label: 'English', available: false },
                            { code: 'uk', label: 'Українська', available: false }
                        ]
                        Button {
                            id: languageOption
                            required property var modelData
                            objectName: 'interfaceLanguage_' + modelData.code
                            width: parent.width
                            height: 48
                            enabled: modelData.available
                            focusPolicy: Qt.StrongFocus
                            Accessible.name: modelData.label + (enabled ? ', выбран' : ', скоро, недоступен')
                            onActiveFocusChanged: if (activeFocus) settings.reveal(languageOption)
                            background: Rectangle {
                                radius: 10
                                color: languageOption.enabled ? backend.colors.selected : backend.colors.disabled
                                border.width: languageOption.activeFocus ? 2 : 1
                                border.color: languageOption.enabled ? backend.colors.accent : backend.colors.border
                            }
                            contentItem: RowLayout {
                                spacing: 12
                                Copy { Layout.fillWidth: true; text: languageOption.modelData.label; color: languageOption.enabled ? backend.colors.text : backend.colors.disabledText }
                                Copy { text: languageOption.enabled ? '✓ Выбран' : 'Скоро'; color: languageOption.enabled ? backend.colors.accent : backend.colors.disabledText; font.pixelSize: 13 }
                            }
                        }
                    }
                }
                Rectangle { width: parent.width; height: 1; color: backend.colors.border }
                Copy { text: 'Тема интерфейса'; font.pixelSize: 20; font.weight: Font.DemiBold }
                Copy { width: parent.width; text: 'Нажми на скриншот. Тема применится сразу и сохранится для следующего запуска.'; color: backend.colors.muted; font.pixelSize: 14 }
                Flickable {
                    id: themeStrip
                    objectName: 'themeStrip'
                    width: parent.width
                    height: Math.max(180, (width - 36) / 4) * 0.56 + 18
                    contentWidth: themes.width
                    contentHeight: height
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    flickableDirection: Flickable.HorizontalFlick
                    ScrollBar.horizontal: AppScrollBar { policy: ScrollBar.AsNeeded }
                    Row {
                        id: themes
                        objectName: 'themeGrid'
                        spacing: 12
                        Repeater {
                            model: backend.themeIds
                            Button {
                                id: themeCard
                                required property string modelData
                                required property int index
                                objectName: 'themeCard_' + modelData
                                property bool selected: backend.theme === modelData
                                width: Math.max(180, (themeStrip.width - 36) / 4)
                                height: width * 0.56
                                padding: 0
                                hoverEnabled: true
                                focusPolicy: Qt.StrongFocus
                                text: backend.themeNames[index]
                                Accessible.name: text + ' тема' + (selected ? ', выбрана' : ', выбрать')
                                onActiveFocusChanged: if (activeFocus) {
                                    settings.reveal(themeStrip)
                                    if (x < themeStrip.contentX) themeStrip.contentX = x
                                    else if (x + width > themeStrip.contentX + themeStrip.width)
                                        themeStrip.contentX = x + width - themeStrip.width
                                }
                                onClicked: backend.theme = modelData
                                Keys.onReturnPressed: clicked()
                                Keys.onRightPressed: if (index < 3) themes.children[index + 1].forceActiveFocus()
                                Keys.onLeftPressed: if (index > 0) themes.children[index - 1].forceActiveFocus()
                                ToolTip.visible: hovered || activeFocus
                                ToolTip.text: text + (selected ? ' · Выбрана' : '')
                                ToolTip.delay: 500
                                background: Item {}
                                contentItem: ThemePreview {
                                    themeId: themeCard.modelData
                                    cutoutColor: backend.colors.background
                                    outlineColor: themeCard.activeFocus ? backend.colors.text : backend.colors.accent
                                    outlined: themeCard.selected || themeCard.activeFocus || themeCard.hovered
                                    Rectangle {
                                        visible: themeCard.selected
                                        anchors { top: parent.top; right: parent.right; topMargin: 8; rightMargin: 12 }
                                        width: 26; height: 26; radius: 13
                                        color: backend.colors.accent
                                        Text { anchors.centerIn: parent; text: '✓'; font.pixelSize: 18; color: backend.colors.onAccent }
                                    }
                                }
                            }
                        }
                    }
                }
                Copy { visible: themeStrip.contentWidth > themeStrip.width; width: parent.width; text: 'Прокрути ряд вправо или выбери тему стрелками ← →.'; color: backend.colors.muted; font.pixelSize: 13 }
                Rectangle { width: parent.width; height: 1; color: backend.colors.border }
                Copy { text: 'Анимация'; font.pixelSize: 20; font.weight: Font.DemiBold }
                CheckBox {
                    id: motion
                    objectName: 'settingsMotion'
                    width: parent.width
                    implicitHeight: Math.max(48, contentItem.implicitHeight + 16)
                    checked: backend.reducedMotion
                    onActiveFocusChanged: if (activeFocus) settings.reveal(motion)
                    onToggled: backend.reducedMotion = checked
                    focusPolicy: Qt.StrongFocus
                    Accessible.name: 'Меньше анимации'
                    indicator: Rectangle {
                        x: 0; y: (motion.height - height) / 2
                        width: 24; height: 24; radius: 6
                        color: motion.checked ? backend.colors.accent : backend.colors.input
                        border.width: motion.activeFocus ? 2 : 1
                        border.color: motion.activeFocus ? backend.colors.text : backend.colors.border
                        Text { anchors.centerIn: parent; text: motion.checked ? '✓' : ''; color: backend.colors.onAccent; font.pixelSize: 16 }
                    }
                    contentItem: Copy { leftPadding: 38; text: 'Меньше анимации'; verticalAlignment: Text.AlignVCenter }
                }
                Copy { width: parent.width; text: 'Отключает анимацию переходов и фона, чтобы меньше отвлекаться.'; color: backend.colors.muted; font.pixelSize: 14 }
                Rectangle { width: parent.width; height: 1; color: backend.colors.border }
                TutorSettings { reveal: settings.reveal }
                Rectangle { width: parent.width; height: 1; color: backend.colors.border }
                Copy { text: 'PythonTech 0.5.0'; font.pixelSize: 20; font.weight: Font.DemiBold }
                Flow {
                    width: parent.width
                    spacing: 8
                    AppButton {
                        id: updatesButton
                        objectName: 'openUpdates'
                        text: 'Журнал обновлений'
                        onActiveFocusChanged: if (activeFocus) settings.reveal(updatesButton)
                        onClicked: { info.opener = updatesButton; info.about = false; info.open() }
                    }
                    AppButton {
                        id: aboutButton
                        objectName: 'openAbout'
                        text: 'О разработке'
                        onActiveFocusChanged: if (activeFocus) settings.reveal(aboutButton)
                        onClicked: { info.opener = aboutButton; info.about = true; info.open() }
                    }
                }

            }
        }
    }
}
