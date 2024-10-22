from functools import reduce as _reduce
from typing import Optional, List

from PyQt5.QtWidgets import QMessageBox

from trnsysGUI.constants import DEFAULT_MESSAGE_BOX_TITLE, DEFAULT_MESSAGE_BOX_MESSAGE


class MessageBox:

    @classmethod
    def create(
        cls,
        messageBoxTitle: str = DEFAULT_MESSAGE_BOX_TITLE,
        messageText: str = DEFAULT_MESSAGE_BOX_MESSAGE,
        buttons: Optional[List[int]] = None,
        defaultButton: Optional[int] = None,
    ) -> int:
        """
        Configures the QMessageBox

        :param messageBoxTitle: Title of the message box
        :param messageText: Main message content
        :param buttons: List of QMessageBox standard buttons
        :param defaultButton: QMessageBox default button
        """
        msgBox = QMessageBox()
        msgBox.setWindowTitle(messageBoxTitle)
        msgBox.setText(messageText)

        # Clear the default buttons
        msgBox.setStandardButtons(QMessageBox.NoButton)

        # Add custom buttons
        if buttons:
            msgBox.setStandardButtons(_reduce(lambda x, y: x | y, buttons))
            if defaultButton:
                msgBox.setDefaultButton(defaultButton)
        else:
            # Set default buttons (Yes and Cancel) if none are provided
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Cancel)

        return msgBox.exec()
