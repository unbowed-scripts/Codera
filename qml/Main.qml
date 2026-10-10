import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    objectName: 'window'
    width: 1380; height: 940
    minimumWidth: 600; minimumHeight: 600
    visible: true
    color: '#111413'
    title: 'PythonTech'
    property bool inCourse: false
    property bool compact: width < 1000
    property bool drawerOpen: false
    property bool changing: false
    property string pendingKind: ''
    property string pendingKey: ''
    property int transitionRevision: 0
    property int commits: 0

    function enterCourse() { inCourse = true }
    function leaveCourse() { drawerOpen = false; inCourse = false }
    function navigate(kind, key) {
        if (!backend.validRoute(kind, key)) return
        drawerOpen = false
        const target = kind + ':' + key
        if (!changing && target === backend.routeKey) return
        pendingKind = kind; pendingKey = key
        if (changing) return // Coalesce rapid clicks; the most recent target wins.
        backend.saveScroll(backend.routeKey, course.contentY)
        course.stopScroll()
        changing = true
        fadeIn.stop()
        if (backend.reducedMotion) { course.opacity = 0; commitPage() }
        else fadeOut.restart()
    }
    function commitPage() {
        course.opacity = 0
        backend.open(pendingKind, pendingKey)
        commits++
        const revision = ++transitionRevision
        // Finish delegate creation and layout while invisible, then restore scroll.
        Qt.callLater(function() { Qt.callLater(function() {
            if (revision !== transitionRevision) return
            if (pendingKind + ':' + pendingKey !== backend.routeKey) { commitPage(); return }
            course.restoreScroll(backend.restoredScroll())
            changing = false
            if (backend.reducedMotion) course.opacity = 1
            else fadeIn.restart()
        }) })
    }
    NumberAnimation { id: fadeOut; target: course; property: 'opacity'; to: 0; duration: 75; easing.type: Easing.OutQuad; onFinished: window.commitPage() }
    NumberAnimation { id: fadeIn; target: course; property: 'opacity'; from: 0; to: 1; duration: 130; easing.type: Easing.OutCubic }
    Connections {
        target: backend
        function onMotionChanged() {
            if (backend.reducedMotion) {
                fadeOut.stop(); fadeIn.stop()
                if (window.changing) window.commitPage()
                else course.opacity = 1
            }
        }
    }
    header: Rectangle {
        height: 72; color: '#111413'
        Rectangle { height: 1; color: '#303b33'; anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 24; rightMargin: 24 } }
        RowLayout {
            anchors { fill: parent; leftMargin: 28; rightMargin: 24 }
            spacing: 16
            Copy { text: '[p.]'; color: '#a6efbd'; font.pixelSize: 26; font.bold: true }
            Copy { text: 'PythonTech'; font.pixelSize: 15; font.weight: Font.DemiBold }
            Item { Layout.fillWidth: true }
            CheckBox {
                id: motionToggle
                text: 'Меньше анимации'; checked: backend.reducedMotion
                onToggled: backend.reducedMotion = checked
                palette.windowText: '#adb9b0'; palette.highlight: '#a6efbd'
                font.pixelSize: 12
                indicator: Rectangle { x: 4; y: (motionToggle.height - height) / 2; width: 18; height: 18; radius: 5; color: motionToggle.checked ? '#a6efbd' : '#191e1b'; border.color: motionToggle.activeFocus ? '#edf2ee' : '#809588' }
            }
            AppButton { text: 'Сменить язык'; quiet: true; visible: window.inCourse; onClicked: window.leaveCourse() }
        }
    }
    Landing { anchors.fill: parent; shell: window; visible: !window.inCourse; running: visible && window.visible && window.visibility !== Window.Minimized }
    Item {
        anchors { fill: parent; margins: 24; topMargin: 12 }
        visible: window.inCourse
        RowLayout {
            id: stage
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 48; spacing: 8
            Copy { text: 'Учебное пространство'; font.pixelSize: 12; color: '#adb9b0'; visible: !window.compact }
            AppButton { objectName: 'topicsToggle'; visible: window.compact; text: window.drawerOpen ? 'Закрыть темы' : '☰  Темы'; onClicked: window.drawerOpen = !window.drawerOpen }
            Item { Layout.fillWidth: true }
            AppButton { text: 'Джуниор'; selected: true }
            AppButton { text: window.compact ? 'Средний' : 'Средний · скоро'; enabled: false }
            AppButton { text: window.compact ? 'Высокий' : 'Высокий · скоро'; enabled: false }
        }
        Sidebar {
            id: sidebar
            shell: window
            anchors { left: parent.left; top: stage.bottom; bottom: parent.bottom; topMargin: 16 }
            width: 276
            visible: !window.compact
        }
        CourseView {
            id: course
            objectName: 'courseViewport'
            shell: window
            anchors { left: window.compact ? parent.left : sidebar.right; right: parent.right; top: stage.bottom; bottom: parent.bottom; leftMargin: window.compact ? 0 : 28; topMargin: 16 }
            enabled: !window.changing && !window.drawerOpen
        }
        // Overlay navigation never changes the page width or scroll position.
        Rectangle {
            anchors { fill: parent; topMargin: 64 }
            visible: window.compact && window.drawerOpen
            color: '#b0111413'
            z: 2
            MouseArea { anchors.fill: parent; onClicked: window.drawerOpen = false }
            Sidebar { anchors { top: parent.top; left: parent.left; bottom: parent.bottom } width: Math.min(380, parent.width); shell: window }
        }
    }
}
