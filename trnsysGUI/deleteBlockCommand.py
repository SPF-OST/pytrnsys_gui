from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.BlockItem as _bi
import trnsysGUI.common as _com
import trnsysGUI.internalPiping as _ip
import trnsysGUI.names.undo as _nu

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class DeleteBlockCommand(_qtw.QUndoCommand):
    def __init__(
        self,
        blockItem: _bi.BlockItem,
        editor: _ed.Editor,  # type: ignore[name-defined]
        undoNamingHelper: _nu.UndoNamingHelper,
    ) -> None:
        assert isinstance(blockItem, _ip.HasInternalPiping) and isinstance(blockItem, _bi.BlockItem)

        description = f"Delete {blockItem.name}"
        super().__init__(description)

        self._blockItem = blockItem
        self._editor = editor
        self._undoNamingHelper = undoNamingHelper

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
        self._undoNamingHelper.removeNameForDelete(self._blockItem.displayName)

    def undo(self):
        checkDdckFolder = self._blockItem.hasDdckPlaceHolders()
        oldName = self._blockItem.displayName
        generatedNamePrefix = self._blockItem.name

        displayName = self._undoNamingHelper.getOrCreateAndAddNonCollidingNameForAdd(
            oldName, _nu.DeleteCommandTargetType.COMPONENT, checkDdckFolder, generatedNamePrefix
        )
        self._blockItem.setDisplayName(displayName)

        self._editor.trnsysObj.append(self._blockItem)
        self._editor.diagramScene.addItem(self._blockItem)
        self._blockItem.addTree()

        super().undo()
