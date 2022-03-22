from pytrnsys.utils.result import *

import PyQt5.QtWidgets as _qtw


def showErrorMessageBox(_error: Error, title: str) -> None:
    messageBox = _qtw.QMessageBox()
    messageBox.setWindowTitle(title)
    messageBox.setText(_error.message)
    messageBox.exec()
