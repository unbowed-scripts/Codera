import QtQuick
Text {
    color: backend.colors.text
    font.pixelSize: 15
    wrapMode: Text.WordWrap
    textFormat: Text.PlainText
    lineHeight: 1.25
    Accessible.role: Accessible.StaticText
    Accessible.name: text
}
