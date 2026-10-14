import QtQuick
import PythonTech.Terminal 1.0

TerminalSurface {
    objectName: 'terminalSurface'
    session: backend.workspace.terminal
    appearance: backend.workspace.terminalAppearance
    Accessible.role: Accessible.EditableText
    Accessible.name: 'Терминал проекта. Ввод команд; Ctrl+C остановить, Ctrl+Shift+V вставить.'
}
