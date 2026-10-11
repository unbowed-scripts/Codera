import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Card {
    id: nav
    objectName: 'sidebar'
    required property var shell
    property var expanded: ({})
    color: backend.colors.surface
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
        Copy { text: 'ТВОЁ НАПРАВЛЕНИЕ'; font.pixelSize: 11; color: backend.colors.muted; Layout.fillWidth: true }
        AppComboBox {
            id: tracks
            objectName: 'trackSelector'
            Layout.fillWidth: true
            implicitHeight: 44
            model: backend.tracks
            currentIndex: backend.tracks.indexOf(backend.track)
            onActivated: nav.shell.navigate('overview', currentText)
            Accessible.name: 'Направление обучения'
        }
        AppButton { Layout.fillWidth: true; text: '▦  Обзор направления'; selected: backend.kind === 'overview'; onClicked: nav.shell.navigate('overview', backend.track) }
        TextField {
            id: search
            Layout.fillWidth: true
            implicitHeight: 44
            placeholderText: 'Найти тему…'; color: backend.colors.text; placeholderTextColor: backend.colors.muted; selectByMouse: true
            Accessible.name: 'Поиск тем'
            background: Rectangle { color: backend.colors.input; radius: 10; border.color: search.activeFocus ? backend.colors.accent : backend.colors.border }
        }
        ListView {
            id: list
            objectName: 'topicList'
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            flickDeceleration: 6000
            FastScroll { scroller: list }
            model: nav.rows()
            ScrollBar.vertical: AppScrollBar {}
            delegate: Item {
                required property var modelData
                width: list.width; height: 46
                AppButton {
                    anchors { fill: parent; bottomMargin: 4 }
                    text: (modelData.child ? (backend.completedKeys.includes(modelData.key) ? '✓  ' : modelData.available ? '●  ' : '○  ') : (nav.expanded[modelData.key] ? '⌄  ' : '›  ')) + modelData.title
                    quiet: true
                    selected: backend.routeKey === (modelData.child ? 'lesson:' : 'section:') + modelData.key
                    contentItem: Text { text: parent.text; font.pixelSize: 13; color: parent.selected ? backend.colors.accent : backend.colors.text; elide: Text.ElideRight; verticalAlignment: Text.AlignVCenter; leftPadding: modelData.child ? 12 : 0 }
                    onClicked: {
                        if (!modelData.child) {
                            let e = Object.assign({}, nav.expanded); e[modelData.key] = !e[modelData.key]; nav.expanded = e
                        }
                        nav.shell.navigate(modelData.child ? 'lesson' : 'section', modelData.key)
                    }
                }
            }
            Copy { visible: list.count === 0; width: parent.width; text: 'Таких тем нет'; color: backend.colors.muted; font.pixelSize: 13 }
        }
        Copy { Layout.fillWidth: true; text: 'Пройдено ' + backend.progress.done + ' из ' + backend.progress.total + ' · доступно ' + backend.progress.ready; font.pixelSize: 12; color: backend.colors.muted }
        Rectangle {
            Layout.fillWidth: true; height: 4; radius: 2; color: backend.colors.border
            Rectangle { height: parent.height; width: parent.width * backend.progress.done / Math.max(1, backend.progress.total); radius: 2; color: backend.colors.accent }
        }
        AppButton { Layout.fillWidth: true; quiet: true; text: 'Как устроено обучение  ↗'; onClicked: nav.shell.navigate('route', 'guide') }
    }
}
