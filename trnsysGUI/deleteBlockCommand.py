from __future__ import annotations

import pathlib as _pl
import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.BlockItem as _bi
import trnsysGUI.blockItemHasInternalPiping as _biip
import trnsysGUI.common as _com
import trnsysGUI.components.ddckFolderHelpers as _dfh
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
        assert isinstance(blockItem, _biip.BlockItemHasInternalPiping)

        description = f"Delete {blockItem.name}"
        super().__init__(description)

        self._blockItem = blockItem
        self._editor = editor
        self._undoNamingHelper = undoNamingHelper
        self._trashedDdckDirPath: _pl.Path | None = None

        self._createChildDeleteConnectionUndoCommands(blockItem)

    def _createChildDeleteConnectionUndoCommands(self, blockItem):
        portItems = [*blockItem.inputs, *blockItem.outputs]

        connections = {
            connection
            for p in portItems
            if (connection := _com.getSingleOrNone(p.connectionList))
            is not None
        }

        for connection in connections:
            connection.createDeleteUndoCommand(self)

    def redo(self):
        super().redo()

        self._blockItem.deleteBlock()
        self._undoNamingHelper.removeNameForDelete(self._blockItem.displayName)

        # Moved to `ddck/.deleted` (not deleted) so undo can restore it.
        self._trashedDdckDirPath = _dfh.moveComponentDdckFolderToTrash(
            self._blockItem, _pl.Path(self._editor.projectFolder)
        )

    def undo(self):
        checkDdckFolder = self._blockItem.hasDdckDirectory()
        oldName = self._blockItem.displayName
        generatedNamePrefix = self._blockItem.name

        displayName = (
            self._undoNamingHelper.addOrGenerateAndAddAnNonCollidingNameForAdd(
                oldName,
                _nu.DeleteCommandTargetType.COMPONENT,
                checkDdckFolder,
                generatedNamePrefix,
                firstGeneratedNameHasNumber=True,
            )
        )
        self._blockItem.setDisplayName(displayName)
        self._restoreDdckFolder(displayName)

        self._editor.trnsysObj.append(self._blockItem)
        self._editor.diagramScene.addItem(self._blockItem)

        super().undo()

    def _restoreDdckFolder(self, displayName: str) -> None:
        if not self._trashedDdckDirPath:
            return
        projectDirPath = _pl.Path(self._editor.projectFolder)
        isRestored = _dfh.restoreComponentDdckFolderFromTrash(
            self._trashedDdckDirPath, displayName, projectDirPath
        )
        if isRestored:
            self._trashedDdckDirPath = None
            return
        _qtw.QMessageBox.warning(
            None,
            "ddck folder not restored",
            f"The ddck folder of `{displayName}` could not be restored. It's"
            f" still in `{self._trashedDdckDirPath}`.",
        )
