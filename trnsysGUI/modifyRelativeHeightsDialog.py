import dataclasses as _dc
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qwt

NewHeight = _tp.Union[float, _tp.Literal["empty"]]


@_dc.dataclass
class NewRelativeHeights:
    input: NewHeight
    output: NewHeight


class ModifyRelativeHeightsDialog(_qwt.QDialog):
    """
    A dialog box lets the user choose the path and the name of folder for a new project
    """

    def __init__(self, relativeInputHeight: float, relativeOutputHeight: float, parent=None):
        super().__init__(parent)

        self.newRelativeHeights: _tp.Optional[NewRelativeHeights] = None

        inputLabel = _qwt.QLabel(f"New input height (was {relativeInputHeight * 100:.0f}%): ")
        self._inputLineEdit = _qwt.QLineEdit()
        inputLayout = _qwt.QHBoxLayout()
        inputLayout.addWidget(inputLabel)
        inputLayout.addWidget(self._inputLineEdit)

        outputLabel = _qwt.QLabel(f"New output height (was {relativeOutputHeight * 100:.0f}%): ")
        self._outputLineEdit = _qwt.QLineEdit()
        outputLayout = _qwt.QHBoxLayout()
        outputLayout.addWidget(outputLabel)
        outputLayout.addWidget(self._outputLineEdit)

        okButton = _qwt.QPushButton("Done")
        okButton.setFixedWidth(50)
        buttonLayout = _qwt.QHBoxLayout()
        buttonLayout.addWidget(okButton, alignment=_qtc.Qt.AlignCenter)

        overallLayout = _qwt.QVBoxLayout()
        overallLayout.addLayout(inputLayout)
        overallLayout.addLayout(outputLayout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(400)

        okButton.clicked.connect(self._onOk)
        self.setWindowTitle("Modify direct port couple")
        self.exec()

    def _onOk(self):
        inputText = self._inputLineEdit.text()
        newRelativeInputHeight = self._getNewRelativeHeight(inputText, "input")
        if not newRelativeInputHeight:
            return

        outputText = self._outputLineEdit.text()
        newRelativeOutputHeight = self._getNewRelativeHeight(outputText, "output")
        if not newRelativeOutputHeight:
            return

        self.newRelativeHeights = NewRelativeHeights(newRelativeInputHeight, newRelativeOutputHeight)

        self.close()

    @classmethod
    def _getNewRelativeHeight(cls, relativeHeightInPercentAsText: str, portName: str) -> _tp.Optional[NewHeight]:
        if not relativeHeightInPercentAsText:
            return "empty"

        try:
            relativeHeightInPercent = int(relativeHeightInPercentAsText)
        except ValueError:
            cls._showFormattingError(portName)
            return None

        if not 1 <= relativeHeightInPercent <= 99:
            cls._showFormattingError(portName)
            return None

        return relativeHeightInPercent / 100

    @staticmethod
    def _showFormattingError(portName: str) -> None:
        messageBox = _qwt.QMessageBox()
        messageBox.setText(
            f"Value for '{portName}' must be an integer between 1 and 99 inclusive."
        )
        messageBox.exec()
