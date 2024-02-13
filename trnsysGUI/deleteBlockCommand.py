from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res

import trnsysGUI.BlockItem as _bi
import trnsysGUI.common as _com
import trnsysGUI.errors as _errors
import trnsysGUI.internalPiping as _ip

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class DeleteBlockCommand(_qtw.QUndoCommand):
    def __init__(self, blockItem: _bi.BlockItem, editor: _ed.Editor):  # type: ignore[name-defined]
        assert isinstance(blockItem, _ip.HasInternalPiping) and isinstance(blockItem, _bi.BlockItem)

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
        self._editor.componentAndPipeNameValidator.removeName(self._blockItem.displayName)

    def undo(self):
        displayName = self._getNonCollidingDisplayName()
        self._blockItem.setDisplayName(displayName)

        self._editor.trnsysObj.append(self._blockItem)
        self._editor.diagramScene.addItem(self._blockItem)
        self._blockItem.addTree()

        super().undo()

    def _getNonCollidingDisplayName(self) -> str:
        checkDdckFolder = self._blockItem.hasDdckPlaceHolders()
        result = self._editor.componentAndPipeNameValidator.validateName(self._blockItem.displayName, checkDdckFolder)
        if not _res.isError(result):
            return self._blockItem.displayName

        generatedName = self._editor.componentAndPipeNameValidator.generateName(self._blockItem.name, checkDdckFolder)
        errorMessage = (
            f'Could not use previous name "{self._blockItem.displayName}" of component as it '
            f"has been used for other components or pipes in the meantime. The newly generated "
            f'name "{generatedName}" will be used instead. You might want to change it to a more '
            f"meaningful value manually."
        )
        _errors.showErrorMessageBox(errorMessage, title="Name changed")

        return generatedName
