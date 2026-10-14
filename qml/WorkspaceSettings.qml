import QtQuick
import QtQuick.Controls

Column {
    id: settings
    spacing: 12
    property var reveal: function(item) {}
    property var ws: backend.workspace
    Copy { width: parent.width; text: 'Проекты, Python и терминал'; font.pixelSize: 20; font.weight: Font.DemiBold }
    Column {
        width: parent.width
        visible: !settings.ws.active
        height: visible ? implicitHeight : 0
        spacing: 12
    Copy { width: parent.width; text: 'У каждого урока своя папка. Изменение папки проектов не переносит старые файлы. Пути можно менять, когда рабочее пространство закрыто.'; color: backend.colors.muted }
    Copy { text: 'Папка проектов' }
    TutorField { id: root; onActiveFocusChanged: if (activeFocus) settings.reveal(root); width: parent.width; text: settings.ws.root; enabled: !settings.ws.active }
    Copy { width: parent.width; text: 'Оболочка встроенного терминала (пусто — системная)' }
    TutorField { id: shell; onActiveFocusChanged: if (activeFocus) settings.reveal(shell); width: parent.width; text: settings.ws.shell; placeholderText: 'Путь к оболочке'; enabled: !settings.ws.active }
    Copy { width: parent.width; text: 'Программа внешнего терминала (пусто — найти автоматически)' }
    TutorField { id: external; onActiveFocusChanged: if (activeFocus) settings.reveal(external); width: parent.width; text: settings.ws.external; placeholderText: 'Путь к терминалу'; enabled: !settings.ws.active }
    Copy { width: parent.width; text: 'Аргументы внешнего терминала: JSON-список. {project} заменяется путём проекта. Например, для Windows Terminal: ["-d", "{project}"], для Konsole: ["--workdir", "{project}"].'; color: backend.colors.muted }
    TutorField { id: args; onActiveFocusChanged: if (activeFocus) settings.reveal(args); width: parent.width; text: settings.ws.arguments; enabled: !settings.ws.active }
    AppButton { id: savePaths; onActiveFocusChanged: if (activeFocus) settings.reveal(savePaths); text: 'Сохранить пути'; enabled: !settings.ws.active && !settings.ws.runtime.busy; onClicked: settings.ws.configure(root.text, shell.text, external.text, args.text) }
    Copy { width: parent.width; text: settings.ws.status; color: backend.colors.muted }
    }
    Copy { width: parent.width; text: 'Python для учебных проектов'; font.pixelSize: 18; font.weight: Font.DemiBold }
    Copy { width: parent.width; text: 'Скачать Python 3.13: uv загрузит сборку Astral python-build-standalone в папку данных PythonTech. Нужен интернет. Системный Python не заменяется. Перед открытием терминала приложение предложит подготовить окружение с pip, а для Web — также с Flask и requests.'; color: backend.colors.muted }
    TutorField { id: pythonPath; onActiveFocusChanged: if (activeFocus) settings.reveal(pythonPath); width: parent.width; text: settings.ws.runtime.python; placeholderText: 'Путь к Python'; enabled: !settings.ws.runtime.busy }
    Flow {
        width: parent.width; spacing: 8
        AppButton { id: choosePython; onActiveFocusChanged: if (activeFocus) settings.reveal(choosePython); text: 'Выбрать этот Python'; enabled: !settings.ws.runtime.busy; onClicked: settings.ws.runtime.selectPython(pythonPath.text) }
        AppButton { id: downloadPython; onActiveFocusChanged: if (activeFocus) settings.reveal(downloadPython); text: 'Скачать Python 3.13'; enabled: !settings.ws.runtime.busy; onClicked: settings.ws.runtime.downloadPython() }
        AppButton { id: cancelInstall; onActiveFocusChanged: if (activeFocus) settings.reveal(cancelInstall); text: 'Отменить установку'; visible: settings.ws.runtime.busy; onClicked: settings.ws.runtime.cancel() }
    }
    BusyIndicator { running: settings.ws.runtime.busy; visible: running; width: 32; height: 32 }
    Copy { width: parent.width; text: settings.ws.runtime.status; color: backend.colors.muted }
    Copy { width: parent.width; text: settings.ws.runtime.log; visible: text.length > 0; font.family: 'monospace'; font.pixelSize: 12 }
}
