import QtQuick
import QtQuick.Controls

Flickable {
    id: view
    required property var shell
    clip: true
    boundsBehavior: Flickable.StopAtBounds
    flickableDirection: Flickable.VerticalFlick
    flickDeceleration: 6000
    FastScroll { scroller: view }
    contentWidth: width
    contentHeight: loader.height + 32
    function stopScroll() { cancelFlick() }
    function restoreScroll(y) { contentY = Math.max(0, Math.min(y, contentHeight - height)) }
    ScrollBar.vertical: AppScrollBar {}
    Loader {
        id: loader
        objectName: 'pageLoader'
        width: Math.min(parent.width - 12, backend.kind === 'lesson' ? 920 : 1080)
        x: Math.max(0, (parent.width - width) / 2)
        y: 0
        sourceComponent: backend.kind === 'overview' ? overview : backend.kind === 'section' ? section : backend.kind === 'lesson' ? lesson : route
    }
    Component { id: overview; Overview { shell: view.shell } }
    Component { id: section; SectionPage { shell: view.shell } }
    Component { id: lesson; LessonPage { shell: view.shell } }
    Component { id: route; RoutePage { shell: view.shell } }
}
