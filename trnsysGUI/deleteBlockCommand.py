from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.common as _com

import trnsysGUI.BlockItem as _bi
import trnsysGUI.PortItemBase as _pi
import trnsysGUI.connection.connectionBase as _cb

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class DeleteBlockCommand(_qtw.QUndoCommand):
    def __init__(self, blockItem: _bi.BlockItem, editor: _ed.Editor):  # type: ignore[name-defined]
        description = f"Delete {blockItem.name}"
        super().__init__(description)

        self._blockItem = blockItem
        self._editor = editor

        self._createChildDeleteConnectionUndoCommands(blockItem)

    def _createChildDeleteConnectionUndoCommands(self, blockItem):
        self._createChildDeleteConnectionUndoCommandsForPorts(blockItem.inputs)
        self._createChildDeleteConnectionUndoCommandsForPorts(blockItem.outputs)

    def _createChildDeleteConnectionUndoCommandsForPorts(
        self, ports: _tp.Sequence[_pi.PortItemBase]  # type: ignore[name-defined]
    ) -> None:
        connections: _tp.Sequence[_cb.ConnectionBase] = [  # type: ignore[name-defined]
            connection for p in ports if (connection := _com.getSingleOrNone(p.connectionList)) is not None
        ]

        for connection in connections:
            connection.createDeleteUndoCommand(self)

    def redo(self):
        super().redo()

        self._blockItem.deleteBlock()

    def undo(self):
        self._editor.trnsysObj.append(self._blockItem)
        self._editor.diagramScene.addItem(self._blockItem)
        self._blockItem.addTree()

        super().undo()
