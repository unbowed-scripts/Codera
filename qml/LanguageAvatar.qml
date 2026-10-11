import QtQuick

Rectangle {
    required property string languageKey
    width: 60; height: 60; radius: 16
    color: '#f3f5f8'
    Accessible.ignored: true
    Image {
        objectName: 'languageAvatar_' + parent.languageKey
        anchors { fill: parent; margins: 10 }
        source: 'icons/languages/' + parent.languageKey + '.svg'
        sourceSize.width: 96; sourceSize.height: 96
        fillMode: Image.PreserveAspectFit
        smooth: true
    }
}
