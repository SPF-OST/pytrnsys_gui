import PyQt5.QtWidgets as _qtw


def showErrorMessageBox(errorMessage: str) -> None:
    messageBox = _qtw.QMessageBox()
    messageBox.setWindowTitle("Error")
    messageBox.setText(
        errorMessage
    )
    messageBox.setStandardButtons(_qtw.QMessageBox.Ok)
    messageBox.exec()
