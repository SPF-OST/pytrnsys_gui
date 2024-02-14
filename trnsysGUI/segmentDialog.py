import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res

import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.errors as _err
import trnsysGUI.names.rename as _rename


class SegmentDialog(_qtw.QDialog):
    def __init__(self, connection: _cb.ConnectionBase, renameHelper: _rename.RenameHelper) -> None:
        super().__init__()
        self._connection = connection
        self._renameHelper = renameHelper

        nameLabel = _qtw.QLabel("Name:")
        self._lineEdit = _qtw.QLineEdit(self._connection.displayName)

        okButton = _qtw.QPushButton("OK")
        cancelButton = _qtw.QPushButton("Cancel")

        buttonLayout = _qtw.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        layout = _qtw.QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self._lineEdit, 0, 1)
        layout.addLayout(buttonLayout, 1, 0, 2, 0)
        self.setLayout(layout)

        okButton.clicked.connect(self._acceptedEdit)
        cancelButton.clicked.connect(self._cancel)
        self.setWindowTitle("Change connection name")

    def _acceptedEdit(self) -> None:
        newName = self._lineEdit.text()
        currentName = self._connection.displayName

        checkDdckFolder = False
        result = self._renameHelper.canRename(currentName, newName, checkDdckFolder)
        if _res.isError(result):
            errorMessage = _res.error(result)
            _err.showErrorMessageBox(errorMessage.message)
            return

        self._applyNameChange(newName)
        self._renameHelper.rename(currentName, newName)
        self.close()

    def _applyNameChange(self, newName: str) -> None:
        self._connection.setDisplayName(newName)
        for segment in self._connection.segments:
            segment.setToolTip(newName)

    def _cancel(self) -> None:
        self.close()
