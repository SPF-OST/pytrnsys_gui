# pylint: skip-file
# type: ignore

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QGridLayout,
    QTabWidget,
    QWidget,
    QMessageBox,
)

import trnsysGUI.pump as _pmp


class PumpDlg(QDialog):
    def __init__(self, pump: _pmp.Pump, parent=None):
        super(PumpDlg, self).__init__(parent)
        nameLabel = QLabel("Name:")
        self.block = pump
        self.le = QLineEdit(self.block.label.toPlainText())
        self.setWindowIcon(QIcon(pump.pixmap()))
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        self.hFlipBoxLabel = QLabel("Horizontal Flip")
        self.vFlipBoxLabel = QLabel("Vertical Flip")
        self.hFlipBox = QCheckBox()
        self.vFlipBox = QCheckBox()

        self.vFlipBox.setTristate(False)
        self.hFlipBox.setTristate(False)
        self.hFlipBox.setCheckState(self.block.flippedH * 2)
        self.vFlipBox.setCheckState(self.block.flippedV * 2)

        flipLayout = QHBoxLayout()
        flipLayout.addWidget(self.hFlipBoxLabel)
        flipLayout.addWidget(self.hFlipBox)
        flipLayout.addWidget(self.vFlipBoxLabel)
        flipLayout.addWidget(self.vFlipBox)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        tab1Layout = QGridLayout(self)
        tab1Layout.addWidget(nameLabel, 0, 0)
        tab1Layout.addWidget(self.le, 0, 1)
        tab1Layout.addLayout(flipLayout, 1, 0, 3, 0)

        positionLayout = QHBoxLayout()
        self.PumpPowerLabel = QLabel("Mass Flow Rate")
        self.LineEdit = QLineEdit(str(self.block.massFlowRateInKgPerH))
        self.PumpPowerLabel2 = QLabel("kg/h")
        positionLayout.addWidget(self.PumpPowerLabel)
        positionLayout.addWidget(self.LineEdit)
        positionLayout.addWidget(self.PumpPowerLabel2)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        # Add tabs
        self.tabs.addTab(self.tab1, "Diagram")
        self.tabs.addTab(self.tab2, "Adjust Mass Flow Rate")
        self.tab1.setLayout(tab1Layout)
        self.tab2.setLayout(positionLayout)

        self.layout2 = QGridLayout(self)
        self.layout2.addWidget(self.tabs, 0, 0)
        self.layout2.addLayout(buttonLayout, 2, 0, 3, 0)
        self.setLayout(self.layout2)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.hFlipBox.stateChanged.connect(self.setNewFlipStateH)
        self.vFlipBox.stateChanged.connect(self.setNewFlipStateV)
        self.setWindowTitle("Properties")
        self.show()

    def acceptedEdit(self):
        newName = self.le.text()
        self.setPumpPower()
        if newName.lower() == str(self.block.displayName).lower():
            self.close()
        elif newName == "":
            msgb = QMessageBox()
            msgb.setText("Please Enter a name!")
            msgb.exec()
        elif self.parent().nameExists(newName) or self.parent().nameExistsInDdckFolder(newName):
            msgb = QMessageBox()
            msgb.setText("Name already exist!")
            msgb.exec()
        else:
            self.block.label.setPlainText(newName)
            self.block.displayName = newName
            self.close()

    def setNewFlipStateH(self, state):
        self.block.updateFlipStateH(state)
        self.block.updateSidesFlippedH()

    def setNewFlipStateV(self, state):
        self.block.updateFlipStateV(state)
        self.block.updateSidesFlippedV()

    def setPumpPower(self):
        self.block.massFlowRateInKgPerH = int(self.LineEdit.text())

    def cancel(self):
        self.close()
