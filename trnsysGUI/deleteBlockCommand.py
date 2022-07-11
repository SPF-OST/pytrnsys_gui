from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.BlockItem as _bi
import trnsysGUI.common as _com

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
        portItems = [*blockItem.inputs, *blockItem.outputs]

        connections = {
            connection for p in portItems if (connection := _com.getSingleOrNone(p.connectionList)) is not None
        }

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
