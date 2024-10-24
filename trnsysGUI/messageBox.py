from functools import reduce as _reduce
from typing import Optional, List

from PyQt6 import QtWidgets as _qtw

from trnsysGUI.constants import DEFAULT_MESSAGE_BOX_TITLE, DEFAULT_MESSAGE_BOX_MESSAGE


class MessageBox:

    @classmethod
    def create(
        cls,
        messageBoxTitle: str = DEFAULT_MESSAGE_BOX_TITLE,
        messageText: str = DEFAULT_MESSAGE_BOX_MESSAGE,
        buttons: Optional[List[int]] = None,  # type: ignore
        defaultButton: Optional[int] = None,
    ) -> int:
        """
        Configures the QMessageBox

        :param messageBoxTitle: Title of the message box
        :param messageText: Main message content
        :param buttons: List of QMessageBox standard buttons
        :param defaultButton: QMessageBox default button
        """
        print("Got here")
        app = _qtw.QApplication([])
        msgBox = _qtw.QMessageBox()
        print("after box")
        msgBox.setWindowTitle(messageBoxTitle)
        msgBox.setText(messageText)

        # Clear the default buttons
        msgBox.setStandardButtons(_qtw.QMessageBox.StandardButton.NoButton)

        # Add custom buttons
        if buttons:
            msgBox.setStandardButtons(_reduce(lambda x, y: x | y, buttons))  # type: ignore
            if defaultButton:
                msgBox.setDefaultButton(defaultButton)  # type: ignore
        else:
            # Set default buttons (Yes and Cancel) if none are provided
            msgBox.setStandardButtons(_qtw.QMessageBox.StandardButton.Yes | _qtw.QMessageBox.StandardButton.Cancel)
            msgBox.setDefaultButton(_qtw.QMessageBox.StandardButton.Cancel)

        return msgBox.exec()
