import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes

Item {
    id: landing
    required property var shell
    property bool running: false
    clip: true
    // Retained text nodes; transforms are animated by Qt, not repainted by Python.
    Repeater {
        model: 28
        delegate: Item {
            id: stream
            required property int index
            x: index * landing.width / 28
            width: 18
            height: landing.height * .5
            y: landing.height * .5
            clip: true
            Text {
                id: digits
                text: '0\n1\n{\n0\np\n1\n}\n0\n1\n;\n0\n1'
                color: backend.colors.accent
                font.family: 'monospace'
                font.pixelSize: 12
                opacity: Math.max(0, Math.min(.25, y / Math.max(1, stream.height) * .3))
                y: stream.height * (1 - (stream.index % 9) / 9)
                NumberAnimation on y {
                    from: stream.height + (stream.index % 7) * 36
                    to: -digits.height
                    duration: 13000 + (stream.index % 6) * 1100
                    loops: Animation.Infinite
                    running: landing.running && !backend.reducedMotion
                }
            }
        }
    }
    Column {
        id: intro
        width: parent.width - 32
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * .5 - 180
        spacing: 16
        opacity: 0
        Copy { width: parent.width; text: 'ТВОЙ ПУТЬ НАЧИНАЕТСЯ ЗДЕСЬ'; color: backend.colors.muted; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter }
        Copy { width: parent.width; text: 'Добро пожаловать'; color: backend.colors.accent; font.pixelSize: landing.width < 700 ? 34 : 44; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter }
        Copy { width: parent.width; text: 'Выбери свой язык программирования'; color: backend.colors.muted; font.pixelSize: 17; horizontalAlignment: Text.AlignHCenter }
    }
    OpacityAnimator { id: reveal; target: intro; from: 0; to: 1; duration: 450; easing.type: Easing.InOutCubic }
    function showIntro() {
        reveal.stop()
        if (backend.reducedMotion) intro.opacity = 1
        else reveal.start()
    }
    onRunningChanged: if (running) showIntro(); else reveal.stop()
    Connections { target: backend; function onMotionChanged() { if (backend.reducedMotion) { reveal.stop(); intro.opacity = 1 } } }
    Shape {
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * .5 + 7
        width: 510; height: 140
        ShapePath {
            strokeColor: backend.colors.featureBorder; strokeWidth: 2; fillColor: 'transparent'
            startX: 0; startY: 110
            PathCubic { x: 510; y: 140; control1X: 65; control1Y: -55; control2X: 400; control2Y: -45 }
        }
    }
    AppButton {
        objectName: 'startPython'
        x: parent.width / 2 - 225; y: parent.height * .5 + 14
        width: 210; height: 88
        text: 'Python  ↗\nНачать изучение'; primary: true
        onClicked: shell.enterCourse()
    }
    AppButton { x: parent.width / 2 + 38; y: parent.height * .5 + 52; width: 185; height: 84; text: 'JavaScript\nСкоро'; enabled: false }
    Copy { width: parent.width - 32; anchors.horizontalCenter: parent.horizontalCenter; y: parent.height * .5 + 184; text: 'С маленькой строки начинается большой путь'; color: backend.colors.muted; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter }
}
