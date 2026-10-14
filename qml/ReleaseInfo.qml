import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: info
    objectName: 'releaseInfo'
    property bool about: false
    property var opener: null
    parent: Overlay.overlay
    anchors.centerIn: parent
    implicitWidth: 620
    implicitHeight: 640
    width: Math.min(620, parent.width - 32)
    height: Math.min(640, parent.height - 32)
    padding: width < 400 ? 16 : 24
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    onOpened: { infoScroll.contentY = 0; closeInfo.forceActiveFocus() }
    onClosed: if (opener) opener.forceActiveFocus()
    background: Rectangle { radius: 18; color: backend.colors.background; border.color: backend.colors.border }
    Overlay.modal: Rectangle { color: backend.colors.overlay }
    contentItem: ColumnLayout {
        spacing: 16
        Copy { Layout.fillWidth: true; text: info.about ? 'О разработке' : 'Журнал обновлений'; font.pixelSize: 26; font.weight: Font.DemiBold }
        Flickable {
            id: infoScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: body.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: AppScrollBar {}
            FastScroll { scroller: infoScroll }
            Copy {
                id: body
                objectName: 'releaseInfoText'
                width: parent.width - 14
                textFormat: Text.RichText
                text: info.about
                    ? '<p><b>PythonTech</b> · версия ' + Qt.application.version + '</p>'
                      + '<p>Автор: <b>Unbowed / byteix</b>.</p>'
                      + '<p>Бесплатный проект с открытым исходным кодом для изучения программирования. Код распространяется по лицензии MIT.</p>'
                      + '<p>В каждом уроке есть правило, пример и практика. Объяснения написаны простыми словами и разделены на короткие части.</p>'
                      + '<p>Читай теорию, разбирай примеры и пиши свой код. Уроки доступны без аккаунта и интернета. Подключение к внешнему ИИ необязательно.</p>'
                    : '<p><b>0.8.0 · Рабочее пространство · локальная проверка</b></p>'
                      + '<p>Редактор файлов, терминал в отдельном окне с настройкой шрифта и темы, внешний терминал, проекты по урокам и список задач. Загрузка Python и отдельные окружения Core и Web. API-ключи можно сохранять в защищённом системном хранилище.</p>'
                      + '<p><b>0.7.0 · Компактные учебные данные</b></p>'
                      + '<p>В готовых сборках уроки хранятся в сжатом архиве и загружаются при открытии. В памяти остаётся не более 12 последних уроков в кэше.</p>'
                      + '<p>Навигация использует заранее подготовленные списки уроков. Сохранённый прогресс совместим с предыдущей версией. Обучение работает офлайн.</p>'
                      + '<p><b>0.6.0 · Расширенный Python Web</b></p>'
                      + '<p>42 урока, семь мини-проектов и три приложения: заметки, каталог книг и личные задачи. Связанные данные, пользователи, права и запуск.</p>'
                      + '<p><b>0.5.0 · Python Web и подсказки с кодом</b></p>'
                      + '<ul><li>24 урока Python Web: HTTP, Flask, SQLite, безопасность и тестирование.</li>'
                      + '<li>Четыре итоговых теста и мини-проекта. Локальный сервис заметок с HTML и JSON API.</li>'
                      + '<li>Примеры кода в подсказках практики.</li>'
                      + '<li>Подключение своей ИИ-модели с контекстом текущего задания.</li>'
                      + '<li>Обновлённая инструкция для пользователей.</li></ul>'
                      + '<p><b>0.4.0 · Настройки и обучение</b></p>'
                      + '<p><b>Добавлено</b></p><ul>'
                      + '<li>Меню языка интерфейса: русский доступен; English и Українська готовятся.</li>'
                      + '<li>Выбор четырёх тем в ряд с реальными скриншотами и диагональными краями.</li>'
                      + '<li>Журнал обновлений и страница об авторе и идее проекта.</li>'
                      + '<li>Итоговые тесты, мини-проекты и подсказки для разделов Python Core.</li>'
                      + '<li>Каталог языков с аватарками и программами будущих курсов.</li></ul>'
                      + '<p><b>Изменено</b></p><ul>'
                      + '<li>Объяснения уроков разбиты на короткие абзацы с выделением главного.</li>'
                      + '<li>Настройки адаптируются к узкому окну и доступны с клавиатуры.</li>'
                      + '<li>Документация дополнена схемами и описанием релиза.</li></ul>'
                      + '<p><b>0.3.0</b></p><p>Предыдущая настольная версия. Подробности доступны в описании опубликованного релиза.</p>'
            }
        }
        AppButton { id: closeInfo; objectName: 'closeInfo'; text: 'Закрыть'; Layout.alignment: Qt.AlignRight; onClicked: info.close() }
    }
}
