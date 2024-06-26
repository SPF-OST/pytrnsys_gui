import pathlib as _pl

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res
import trnsysGUI.BlockItem as _bi
import trnsysGUI.components.ddckFolderHelpers as _dfh
import trnsysGUI.internalPiping as _ip
import trnsysGUI.names.rename as _rename
import trnsysGUI.warningsAndErrors as _werrors


class ChangeNameDialogBase(_qtw.QDialog):
    def __init__(self, blockItem: _bi.BlockItem, renameHelper: _rename.RenameHelper, projectDirPath: _pl.Path) -> None:
        super().__init__()

        self._blockItem = blockItem
        self._renameHelper = renameHelper
        self._projectDirPath = projectDirPath

        self._displayNameLineEdit = _qtw.QLineEdit(self._blockItem.displayName)

        self.setModal(True)

    def acceptedEdit(self) -> None:
        newName = self._displayNameLineEdit.text()
        oldName = self._blockItem.displayName

        hasDdckFolder = (
            self._blockItem.hasDdckPlaceHolders() if isinstance(self._blockItem, _ip.HasInternalPiping) else False
        )
        result = self._renameHelper.canRename(oldName, newName, hasDdckFolder)

        if _res.isError(result):
            errorMessage = _res.error(result).message
            _werrors.showMessageBox(errorMessage)
            self._displayNameLineEdit.setText(oldName)
            return

        _dfh.moveComponentDdckFolderIfNecessary(self._blockItem, newName, oldName, self._projectDirPath)

        self._blockItem.setDisplayName(newName)
        self._renameHelper.rename(oldName, newName)
        self.close()
