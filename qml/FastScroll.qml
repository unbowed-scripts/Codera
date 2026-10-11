import QtQuick

WheelHandler {
    required property var scroller
    target: null
    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
    // No delayed wheel animation: one notch moves three readable text lines.
    onWheel: function(event) {
        const delta = event.pixelDelta.y !== 0 ? event.pixelDelta.y : event.angleDelta.y * 0.8
        if (delta === 0) { event.accepted = false; return }
        scroller.cancelFlick()
        const top = scroller.originY
        const bottom = top + Math.max(0, scroller.contentHeight - scroller.height)
        scroller.contentY = Math.max(top, Math.min(bottom, scroller.contentY - delta))
        event.accepted = true
    }
}
