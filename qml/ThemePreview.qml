import QtQuick

// Keep the real screenshot upright; cover its corners with diagonal cutouts.
Item {
    id: preview
    required property string themeId
    required property color cutoutColor
    property color outlineColor: backend.colors.accent
    property bool outlined: false
    property real inset: Math.min(22, width * 0.12)
    Image {
        objectName: 'themePreview_' + preview.themeId
        anchors.fill: parent
        source: 'previews/' + preview.themeId + '.png'
        fillMode: Image.PreserveAspectCrop
        smooth: true
        Accessible.ignored: true
    }
    Canvas {
        id: cutouts
        anchors.fill: parent
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        Connections { target: preview; function onCutoutColorChanged() { cutouts.requestPaint() }
            function onOutlineColorChanged() { cutouts.requestPaint() }
            function onOutlinedChanged() { cutouts.requestPaint() } }
        onPaint: {
            const ctx = getContext('2d')
            ctx.reset()
            ctx.fillStyle = preview.cutoutColor
            ctx.beginPath()
            ctx.moveTo(0, 0); ctx.lineTo(preview.inset, 0); ctx.lineTo(0, height)
            ctx.closePath(); ctx.fill()
            ctx.beginPath()
            ctx.moveTo(width, 0); ctx.lineTo(width, height); ctx.lineTo(width - preview.inset, height)
            ctx.closePath(); ctx.fill()
            if (preview.outlined) {
                ctx.strokeStyle = preview.outlineColor
                ctx.lineWidth = 3
                ctx.beginPath()
                ctx.moveTo(preview.inset + 1, 1.5)
                ctx.lineTo(width - 2, 1.5)
                ctx.lineTo(width - preview.inset - 1, height - 1.5)
                ctx.lineTo(2, height - 1.5)
                ctx.closePath(); ctx.stroke()
            }
        }
    }
}
