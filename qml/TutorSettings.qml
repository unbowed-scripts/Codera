import QtQuick
import QtQuick.Controls

Column {
    id: settings
    required property var reveal
    width: parent.width
    spacing: 12
    Copy { width: parent.width; text: 'ИИ-помощник'; font.pixelSize: 20; font.weight: Font.DemiBold }
    Copy { width: parent.width; text: 'Подключи модель с совместимым Chat Completions API. Адрес, название модели и ключ возьми у своего провайдера. Для локального сервера ключ может быть пустым.'; color: backend.colors.muted }
    Copy { width: parent.width; text: 'Адрес API'; font.weight: Font.DemiBold }
    TutorField {
        id: url
        objectName: 'aiUrl'
        width: parent.width
        text: backend.tutor.url
        placeholderText: 'https://…/v1'
        onActiveFocusChanged: if (activeFocus) settings.reveal(url)
    }
    Copy { width: parent.width; text: 'Название модели'; font.weight: Font.DemiBold }
    TutorField {
        id: model
        objectName: 'aiModel'
        width: parent.width
        text: backend.tutor.model
        placeholderText: 'Название модели'
        onActiveFocusChanged: if (activeFocus) settings.reveal(model)
    }
    Copy { width: parent.width; text: 'API-ключ'; font.weight: Font.DemiBold }
    TutorField {
        id: key
        objectName: 'aiKey'
        width: parent.width
        echoMode: TextInput.Password
        placeholderText: 'API-ключ'
        onActiveFocusChanged: if (activeFocus) settings.reveal(key)
    }
    Copy { width: parent.width; text: 'Сохраняются только адрес и название модели. Подключение отправит короткий проверочный запрос; провайдер может учитывать его в оплате. Учебные данные отправляются только по кнопке «Получить подсказку».'; color: backend.colors.muted; font.pixelSize: 12 }
    Flow {
        width: parent.width
        spacing: 8
        AppButton {
            id: connect
            objectName: 'aiConnect'
            text: 'Подключить и проверить'
            enabled: !backend.tutor.busy
            onActiveFocusChanged: if (activeFocus) settings.reveal(connect)
            onClicked: { backend.tutor.connectModel(url.text, model.text, key.text); key.clear() }
        }
        AppButton {
            id: disconnect
            text: 'Отключить'
            onActiveFocusChanged: if (activeFocus) settings.reveal(disconnect)
            onClicked: { backend.tutor.disconnectModel(); key.clear() }
        }
    }
    Copy { objectName: 'aiStatus'; width: parent.width; text: backend.tutor.status; color: backend.tutor.connected ? backend.colors.accent : backend.colors.muted }
}
