import typing as _tp

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res
import trnsysGUI.componentAndPipeNameValidator as _cpn
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.errors as _err


class SegmentDialog(_qtw.QDialog):
    def __init__(self, connection: _cb.ConnectionBase, existingNames: _tp.Sequence[str]) -> None:
        super().__init__()
        self._connection = connection
        self._nameValidator = _cpn.ComponentAndPipeNameValidator(existingNames)

        nameLabel = _qtw.QLabel("Name:")
        self._lineEdit = _qtw.QLineEdit(self._connection.displayName)

        self.okButton = _qtw.QPushButton("OK")
        self.cancelButton = _qtw.QPushButton("Cancel")

        buttonLayout = _qtw.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = _qtw.QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self._lineEdit, 0, 1)
        layout.addLayout(buttonLayout, 1, 0, 2, 0)
        self.setLayout(layout)

        self.okButton.clicked.connect(self._acceptedEdit)
        self.cancelButton.clicked.connect(self._cancel)
        self.setWindowTitle("Change connection name")

    def _acceptedEdit(self) -> None:
        newName = self._lineEdit.text()
        if self._isOldName(newName):
            self.close()
            return

        result = self._nameValidator.validateName(newName)
        if _res.isError(result):
            errorMessage = _res.error(result)
            _err.showErrorMessageBox(errorMessage.message)
            return

        self._applyNameChange(newName)
        self.close()

    def _applyNameChange(self, newName: str) -> None:
        self._connection.setDisplayName(newName)
        for segment in self._connection.segments:
            segment.setToolTip(newName)

    def _isOldName(self, newName: str) -> bool:
        oldName = self._connection.displayName

        return newName.lower() == oldName.lower()

    def _cancel(self) -> None:
        self.close()
