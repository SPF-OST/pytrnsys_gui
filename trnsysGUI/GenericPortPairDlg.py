# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
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
        nameLabel = QLabel("Name:")
        objectLabel = QLabel("Object:" + str(self.block))
        self.le = QLineEdit("0")

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
        self.cancelButton = QPushButton("Close")

        self.addButton.clicked.connect(self.addPortPair)
        self.cancelButton.clicked.connect(self.cancel)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addWidget(self.cancelButton)

        radioButtonLayout = QHBoxLayout()
        self.oButton = QRadioButton("Output")
        self.iButton = QRadioButton("Input")
        radioButtonLayout.addWidget(self.iButton)
        radioButtonLayout.addWidget(self.oButton)

        listWLabel = QLabel("Ports pairs")
        self.listW = QListWidget()

        layout = QGridLayout()
        # layout.addWidget(nameLabel, 0, 0)
        # layout.addWidget(self.le, 0, 1)
        # layout.addLayout(radioButtonLayout, 1, 0, 2, 0)
        layout.addWidget(listWLabel, 0, 0)
        layout.addWidget(self.listW, 1, 0)
        layout.addLayout(positionLayout, 2, 0, 2, 0)
        layout.addLayout(buttonLayout, 5, 0, 2, 0)
        self.setLayout(layout)

        self.setWindowTitle("Change connection name")
        self.loadList()
        self.show()

    def loadList(self):
        print("Loading ports")
        for side in self.block.portPairSides:
            self.listW.addItem("Port pair at " + _SIDE_NAMES[side])

    def addPortPair(self):
        if self.getSide() is not None:
            print("Adding a port")
            self.block.addPortPair(self.getSide())
            self.listW.addItem("Port pair at " + _SIDE_NAMES[self.getSide()])

    def removePortPair(self):
        if self.getSide() is not None:
            self.block.removePortPairOnSide(self.getSide())

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
