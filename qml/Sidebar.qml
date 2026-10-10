import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Card {
    id: nav
    objectName: 'sidebar'
    required property var shell
    property var expanded: ({})
    color: '#191e1b'
    border.width: 0
    function rows() {
        let rows = [], sections = backend.sections, query = search.text.toLowerCase().trim()
        for (let s of sections) {
            let children = s.levels.filter(l => !query || s.title.toLowerCase().includes(query) || l.title.toLowerCase().includes(query))
            if (query && !children.length) continue
            rows.push({key:s.key, title:s.title, child:false, available:false})
            if (query || expanded[s.key]) for (let l of children) rows.push({key:l.key, title:l.title, child:true, available:l.available})
        }
        return rows
    }
    ColumnLayout {
        anchors { fill: parent; margins: 16 }
        spacing: 12
        Copy { text: 'ТВОЁ НАПРАВЛЕНИЕ'; font.pixelSize: 11; color: '#adb9b0'; Layout.fillWidth: true }
        ComboBox {
            id: tracks
            Layout.fillWidth: true
            implicitHeight: 44
            model: backend.tracks
            currentIndex: backend.tracks.indexOf(backend.track)
            onActivated: nav.shell.navigate('overview', currentText)
            palette.button: '#202722'; palette.buttonText: '#edf2ee'; palette.text: '#edf2ee'; palette.base: '#191e1b'; palette.highlight: '#365c43'
            Accessible.name: 'Направление обучения'
            background: Rectangle { color: '#121814'; radius: 10; border.color: tracks.activeFocus ? '#a6efbd' : '#354039' }
            leftPadding: 12
            contentItem: Text { text: tracks.displayText; color: '#edf2ee'; font.pixelSize: 14; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight; rightPadding: 24 }
        }
        AppButton { Layout.fillWidth: true; text: '▦  Обзор направления'; selected: backend.kind === 'overview'; onClicked: nav.shell.navigate('overview', backend.track) }
        TextField {
            id: search
            Layout.fillWidth: true
            implicitHeight: 44
            placeholderText: 'Найти тему…'; color: '#edf2ee'; placeholderTextColor: '#94a59a'; selectByMouse: true
            Accessible.name: 'Поиск тем'
            background: Rectangle { color: '#121814'; radius: 10; border.color: search.activeFocus ? '#a6efbd' : '#354039' }
        }
        ListView {
            id: list
            objectName: 'topicList'
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: nav.rows()
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: Item {
                required property var modelData
                width: list.width; height: 46
                AppButton {
                    anchors { fill: parent; bottomMargin: 4 }
                    text: (modelData.child ? (backend.completedKeys.includes(modelData.key) ? '✓  ' : modelData.available ? '●  ' : '○  ') : (nav.expanded[modelData.key] ? '⌄  ' : '›  ')) + modelData.title
                    quiet: true
                    selected: backend.routeKey === (modelData.child ? 'lesson:' : 'section:') + modelData.key
                    contentItem: Text { text: parent.text; font.pixelSize: 13; color: parent.selected ? '#a6efbd' : '#dce6df'; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter; leftPadding: modelData.child ? 12 : 0 }
                    ToolTip.visible: hovered
                    ToolTip.text: modelData.title
                    onClicked: {
                        if (!modelData.child) {
                            let e = Object.assign({}, nav.expanded); e[modelData.key] = !e[modelData.key]; nav.expanded = e
                        }
                        nav.shell.navigate(modelData.child ? 'lesson' : 'section', modelData.key)
                    }
                }
            }
            Copy { visible: list.count === 0; width: parent.width; text: 'Таких тем нет'; color: '#adb9b0'; font.pixelSize: 13 }
        }
        Copy { Layout.fillWidth: true; text: 'Пройдено ' + backend.progress.done + ' из ' + backend.progress.total + ' · доступно ' + backend.progress.ready; font.pixelSize: 12; color: '#adb9b0' }
        Rectangle {
            Layout.fillWidth: true; height: 4; radius: 2; color: '#354039'
            Rectangle { height: parent.height; width: parent.width * backend.progress.done / Math.max(1, backend.progress.total); radius: 2; color: '#a6efbd' }
        }
        AppButton { Layout.fillWidth: true; quiet: true; text: 'Как устроено обучение  ↗'; onClicked: nav.shell.navigate('route', 'guide') }
    }
}
