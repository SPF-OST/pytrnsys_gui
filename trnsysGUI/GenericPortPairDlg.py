# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QGridLayout,
    QDialog,
    QRadioButton,
    QVBoxLayout,
    QListWidget,
)

import trnsysGUI.sideNrs as _snrs

_SIDE_NAMES = {
    _snrs.SideNrs.LEFT: "Left",
    _snrs.SideNrs.TOP: "Top",
    _snrs.SideNrs.RIGHT: "Right",
    _snrs.SideNrs.BOTTOM: "Bottom",
}


class GenericPortPairDlg(QDialog):
    def __init__(self, block, parent=None):
        super(GenericPortPairDlg, self).__init__(parent)
        self.block = block

        positionLayout = QVBoxLayout()
        positionLabel = QLabel("Select a position")

        self.rButtonLeft = QRadioButton("Left")
        self.rButtonTop = QRadioButton("Top")
        self.rButtonRight = QRadioButton("Right")
        self.rButtonBottom = QRadioButton("Bottom")

        positionLayout.addWidget(positionLabel)
        positionLayout.addWidget(self.rButtonLeft)
        positionLayout.addWidget(self.rButtonTop)
        positionLayout.addWidget(self.rButtonRight)
        positionLayout.addWidget(self.rButtonBottom)

        self.addButton = QPushButton("Add port pair")
        self.removeButton = QPushButton("Remove port pair")
        self.cancelButton = QPushButton("Close")

        self.addButton.clicked.connect(self.addPortPair)
        self.removeButton.clicked.connect(self.removePortPair)
        self.cancelButton.clicked.connect(self.cancel)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.removeButton)
        buttonLayout.addWidget(self.cancelButton)

        listWLabel = QLabel("Ports pairs")
        self.listW = QListWidget()
        self.listW.currentRowChanged.connect(self._updateRemoveButton)

        layout = QGridLayout()
        layout.addWidget(listWLabel, 0, 0)
        layout.addWidget(self.listW, 1, 0)
        layout.addLayout(positionLayout, 2, 0, 2, 0)
        layout.addLayout(buttonLayout, 5, 0, 2, 0)
        self.setLayout(layout)

        self.setWindowTitle("Generic block port pairs")
        self.loadList()
        self._updateRemoveButton()
        self.show()

    def loadList(self):
        for side in self.block.portPairSides:
            self.listW.addItem("Port pair at " + _SIDE_NAMES[side])

    def addPortPair(self):
        if self.getSide() is not None:
            self.block.addPortPair(self.getSide())
            self.listW.addItem("Port pair at " + _SIDE_NAMES[self.getSide()])
            self._updateRemoveButton()

    def removePortPair(self):
        row = self.listW.currentRow()
        if not self._canRemovePortPair(row):
            return

        self.block.removePortPair(row)
        self.listW.takeItem(row)
        self._updateRemoveButton()

    def _updateRemoveButton(self):
        row = self.listW.currentRow()
        self.removeButton.setEnabled(self._canRemovePortPair(row))

    def _canRemovePortPair(self, row):
        # A generic block without port pairs couldn't be connected to anything
        return row >= 0 and self.listW.count() > 1

    def getSide(self):
        if self.rButtonLeft.isChecked():
            return _snrs.SideNrs.LEFT
        elif self.rButtonTop.isChecked():
            return _snrs.SideNrs.TOP
        elif self.rButtonRight.isChecked():
            return _snrs.SideNrs.RIGHT
        elif self.rButtonBottom.isChecked():
            return _snrs.SideNrs.BOTTOM
        else:
            return None

    def cancel(self):
        self.close()
