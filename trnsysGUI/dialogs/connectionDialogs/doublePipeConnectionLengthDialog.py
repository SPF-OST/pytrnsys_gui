import dataclasses as _dc

import PyQt5.QtWidgets as _qtw

import trnsysGUI.errors as _er


@_dc.dataclass
class DPConnection:
    lengthInM: float


class DoublePipeConnectionLengthDialog(_qtw.QDialog):
    def __init__(self, connection: "DPConnection"):
        super(DoublePipeConnectionLengthDialog, self).__init__()
        self.lengthContainer = connection
        self.nameLabel = _qtw.QLabel("Length (m):")
        self.lineEdit = _qtw.QLineEdit(str(connection.lengthInM))
        self.okButton = _qtw.QPushButton("OK")
        self.cancelButton = _qtw.QPushButton("Cancel")
        self.setLayout(self._getLayout())
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Properties")

    def _getLayout(self):
        buttonLayout = _qtw.QGridLayout(self)
        buttonLayout.addWidget(self.nameLabel, 0, 0)
        buttonLayout.addWidget(self.lineEdit, 0, 1)
        buttonLayout.addWidget(self.okButton, 1, 0)
        buttonLayout.addWidget(self.cancelButton, 1, 1)
        return buttonLayout

    def acceptedEdit(self):
        text = self.lineEdit.text()
        try:
            lengthInM = _parsePositiveFloat(text)
            self.lengthContainer.lengthInM = lengthInM
            self.close()
        except ValueError:
            _er.showErrorMessageBox(errorMessage="Value must be positive.", title="Almost there")

    def cancel(self):
        self.close()


def _parsePositiveFloat(text: str) -> float:
    value = float(text)

    if value <= 0:
        raise ValueError("Value must be positive.")

    return value