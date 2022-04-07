import PyQt5.QtWidgets as _qtw


def showErrorMessageBox(errorMessage: str, title: str = "Error") -> None:
    messageBox = _qtw.QMessageBox()
    messageBox.setWindowTitle(title)
    messageBox.setText(
        errorMessage
    )
    messageBox.setStandardButtons(_qtw.QMessageBox.Ok)
    messageBox.exec()
