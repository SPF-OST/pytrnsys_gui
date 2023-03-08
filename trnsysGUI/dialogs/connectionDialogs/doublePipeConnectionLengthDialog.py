
import typing as _tp

import PyQt5.QtWidgets as _qtw

if _tp.TYPE_CHECKING:
    pass


class LengthContainer:
    # todo: change to *pipe*
    def __init__(self, lengthInM: float):
        self.lengthInM = lengthInM


class doublePipeConnectionLengthDialog(_qtw.QDialog):
    def __init__(self, container: "LengthContainer"):
        super(doublePipeConnectionLengthDialog, self).__init__()
        self.lengthContainer = container
        self.nameLabel = _qtw.QLabel("Length (m):")
        self.lineEdit = _qtw.QLineEdit(str(container.lengthInM))
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
            self.showError()

    @staticmethod
    def showError():
        # todo: send to errorMessageBox
        messageBox = _qtw.QMessageBox()
        messageBox.setWindowTitle("Almost there")
        messageBox.setText("Value must be positive.")
        messageBox.exec()

    def cancel(self):
        self.close()


def _parsePositiveFloat(text: str) -> float:
    value = float(text)

    if value <= 0:
        raise ValueError("Value must be positive.")

    return value
