# This Python file uses the following encoding: utf-8
import PyQt5.QtWidgets as _qtw


class doublePipeConnectionLengthDialog(_qtw.QDialog):
    def __init__(self, container):
        super(doublePipeConnectionLengthDialog, self).__init__()
        self.lengthContainer = container
        self.nameLabel = _qtw.QLabel("Length (m):")
        self.lineEdit = _qtw.QLineEdit(str(container.lengthInM))
        self.okButton = _qtw.QPushButton("OK")
        self.cancelButton = _qtw.QPushButton("Cancel")
        buttonLayout = _qtw.QGridLayout(self)
        buttonLayout.addWidget(self.nameLabel, 0, 0)
        buttonLayout.addWidget(self.lineEdit, 0, 1)
        buttonLayout.addWidget(self.okButton, 1, 0)
        buttonLayout.addWidget(self.cancelButton, 1, 1)
        self.setLayout(buttonLayout)
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Properties")
        self.exec()

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
        msgb = _qtw.QMessageBox()
        msgb.setText("Value must be positive.")
        msgb.exec()

    def cancel(self):
        self.close()


def _parsePositiveFloat(text: str) -> float:
    value = float(text)

    if value <= 0:
        raise ValueError("Value must be positive.")

    return value
