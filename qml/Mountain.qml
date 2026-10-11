import QtQuick
import QtQuick.Shapes

Item {
    id: mountain
    implicitHeight: width * .48
    Accessible.role: Accessible.Graphic
    Accessible.name: 'Маршрут обучения: семь шагов к вершине, затем повторение'
    Item {
        width: 600; height: 285
        scale: mountain.width / 600
        transformOrigin: Item.TopLeft
        Shape {
            anchors.fill: parent
            ShapePath { strokeWidth: 0; fillColor: backend.colors.selected; startX: 20; startY: 255; PathLine { x: 150; y: 98 } PathLine { x: 268; y: 255 } PathLine { x: 20; y: 255 } }
            ShapePath { strokeWidth: 0; fillColor: backend.colors.art; startX: 115; startY: 255; PathLine { x: 320; y: 18 } PathLine { x: 545; y: 255 } PathLine { x: 115; y: 255 } }
            ShapePath { strokeWidth: 0; fillColor: backend.colors.selected; startX: 320; startY: 18; PathLine { x: 350; y: 175 } PathLine { x: 545; y: 255 } PathLine { x: 320; y: 18 } }
            ShapePath { strokeWidth: 0; fillColor: backend.colors.snow; startX: 320; startY: 18; PathLine { x: 253; y: 96 } PathLine { x: 293; y: 81 } PathLine { x: 312; y: 108 } PathLine { x: 334; y: 78 } PathLine { x: 365; y: 89 } PathLine { x: 320; y: 18 } }
            ShapePath { strokeWidth: 2; strokeColor: backend.colors.accent; fillColor: 'transparent'; startX: 142; startY: 244; PathLine { x: 172; y: 210 } PathLine { x: 201; y: 176 } PathLine { x: 231; y: 141 } PathLine { x: 260; y: 107 } PathLine { x: 290; y: 73 } PathLine { x: 320; y: 38 } }
        }
        Repeater {
            model: 7
            Rectangle {
                required property int index
                x: 129 + index * 29.6; y: 231 - index * 34.3
                width: 26; height: 26; radius: 13
                color: backend.colors.selected; border.color: backend.colors.accent
                Copy { anchors.centerIn: parent; text: index+1; font.pixelSize: 12; color: backend.colors.accent }
            }
        }
    }
}
