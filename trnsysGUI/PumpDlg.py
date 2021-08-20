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

import trnsysGUI.Pump as _pmp


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
        self.PumpPowerLabel = QLabel("Pump Power")
        self.LineEdit = QLineEdit(str(self.block.rndPwr))
        positionLayout.addWidget(self.PumpPowerLabel)
        positionLayout.addWidget(self.LineEdit)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        # Add tabs
        self.tabs.addTab(self.tab1, "Diagram")
        self.tabs.addTab(self.tab2, "Adjust Pump Power")
        self.tab1.setLayout(tab1Layout)
        self.tab2.setLayout(positionLayout)
        # self.tab2 = layout
        # self.tabs.resize(300, 200)

        # self.tabs.addTab(self.tab2, "Tab 2")
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
        print("Changing displayName")
        newName = self.le.text()
        self.setPumpPower()
        if newName.lower() == str(self.block.displayName).lower():
            self.close()
        elif newName != "" and not self.nameExists(newName):
            # self.block.setName(newName)
            self.block.label.setPlainText(newName)
            self.block.displayName = newName
            self.close()
        elif newName == "":
            msgb = QMessageBox()
            msgb.setText("Please Enter a name!")
            msgb.exec()
        elif self.nameExists(newName):
            msgb = QMessageBox()
            msgb.setText("Name already exist!")
            msgb.exec()

    def setNewFlipStateH(self, state):
        self.block.updateFlipStateH(state)

    def setNewFlipStateV(self, state):
        self.block.updateFlipStateV(state)

    def setPumpPower(self):
        self.block.rndPwr = int(self.LineEdit.text())
        self.block.resStr = "Mfr" + self.block.displayName + " = " + self.LineEdit.text() + "\n"

    def cancel(self):
        self.close()

    def nameExists(self, n):
        for t in self.parent().trnsysObj:
            if str(t.displayName).lower() == n.lower():
                return True
        return False
