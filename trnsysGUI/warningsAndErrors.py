import enum as _enum

import PyQt5.QtWidgets as _qtw


class Title(_enum.Enum):
    WARNING = "Warning"
    ERROR = "Error"


def showMessageBox(message: str, title: Title | str = Title.ERROR) -> None:
    messageBox = _qtw.QMessageBox()

    windowTitle = title if isinstance(title, str) else title.value
    messageBox.setWindowTitle(windowTitle)

    messageBox.setText(message)
    messageBox.setStandardButtons(_qtw.QMessageBox.Ok)
    messageBox.exec()
