from PyQt5 import QtWidgets as _qtw

from pytrnsys.utils import result as _res
from trnsysGUI import BlockItem as _bi
from trnsysGUI import warningsAndErrors as _werrors
from trnsysGUI import internalPiping as _ip
from trnsysGUI.names import rename as _rename


class ChangeNameDialogBase(_qtw.QDialog):
    def __init__(self, blockItem: _bi.BlockItem, renameHelper: _rename.RenameHelper) -> None:
        super().__init__()

        self._blockItem = blockItem
        self._renameHelper = renameHelper
        self._displayNameLineEdit = _qtw.QLineEdit(self._blockItem.displayName)

        self.setModal(True)

    def acceptedEdit(self):
        newName = self._displayNameLineEdit.text()
        oldName = self._blockItem.displayName

        assert isinstance(self._blockItem, _ip.HasInternalPiping)

        checkDdckFolder = self._blockItem.hasDdckPlaceHolders()
        result = self._renameHelper.canRename(oldName, newName, checkDdckFolder)

        if _res.isError(result):
            errorMessage = _res.error(result).message
            _werrors.showMessageBox(errorMessage)
            self._displayNameLineEdit.setText(oldName)
            return

        assert isinstance(self._blockItem, _bi.BlockItem)

        self._blockItem.setDisplayName(newName)
        self._renameHelper.rename(oldName, newName)
        self.close()
