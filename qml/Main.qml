import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    objectName: 'window'
    width: 1380; height: 940
    minimumWidth: 600; minimumHeight: 600
    visible: true
    color: backend.colors.background
    palette.window: backend.colors.background
    palette.windowText: backend.colors.text
    palette.text: backend.colors.text
    palette.base: backend.colors.input
    palette.button: backend.colors.button
    palette.buttonText: backend.colors.text
    palette.highlight: backend.colors.accent
    palette.highlightedText: backend.colors.onAccent
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
    NumberAnimation { id: fadeOut; target: course; property: 'opacity'; to: 0; duration: 45; easing.type: Easing.OutQuad; onFinished: window.commitPage() }
    NumberAnimation { id: fadeIn; target: course; property: 'opacity'; from: 0; to: 1; duration: 85; easing.type: Easing.OutCubic }
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
        height: 72; color: backend.colors.background
        Rectangle { height: 1; color: backend.colors.border; anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 24; rightMargin: 24 } }
        RowLayout {
            anchors { fill: parent; leftMargin: 28; rightMargin: 24 }
            spacing: 16
            Copy { text: '[p.]'; color: backend.colors.accent; font.pixelSize: 26; font.bold: true }
            Copy { visible: !window.compact; text: 'PythonTech'; font.pixelSize: 15; font.weight: Font.DemiBold }
            Item { Layout.fillWidth: true }
            AppComboBox {
                objectName: 'themeSelector'
                Layout.preferredWidth: window.compact ? 132 : 154
                model: backend.themeNames
                currentIndex: backend.themeIds.indexOf(backend.theme)
                onActivated: backend.theme = backend.themeIds[currentIndex]
                Accessible.name: 'Цветовая тема'
            }
            CheckBox {
                id: motionToggle
                text: window.compact ? 'Без анимации' : 'Меньше анимации'; checked: backend.reducedMotion
                onToggled: backend.reducedMotion = checked
                palette.windowText: backend.colors.muted; palette.highlight: backend.colors.accent
                font.pixelSize: 12
                indicator: Rectangle { x: 4; y: (motionToggle.height - height) / 2; width: 18; height: 18; radius: 5; color: motionToggle.checked ? backend.colors.accent : backend.colors.surface; border.color: motionToggle.activeFocus ? backend.colors.text : backend.colors.border }
            }
            AppButton { text: window.compact ? 'Язык' : 'Сменить язык'; quiet: true; visible: window.inCourse; onClicked: window.leaveCourse() }
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
            Copy { text: 'Учебное пространство'; font.pixelSize: 12; color: backend.colors.muted; visible: !window.compact }
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
            color: backend.colors.overlay
            z: 2
            MouseArea { anchors.fill: parent; onClicked: window.drawerOpen = false }
            Sidebar { anchors { top: parent.top; left: parent.left; bottom: parent.bottom } width: Math.min(380, parent.width); shell: window }
        }
    }
}
