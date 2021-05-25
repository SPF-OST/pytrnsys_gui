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
    QDoubleSpinBox,
    QMessageBox,
)

import trnsysGUI.TVentil as _vnt


class TVentilDlg(QDialog):
    def __init__(self, ventil: _vnt.TVentil, parent=None):
        super(TVentilDlg, self).__init__(parent)
        nameLabel = QLabel("Name:")

        self.logger = parent.logger

        self.block = ventil
        self.valvePosition = self.block.positionForMassFlowSolver
        self.le = QLineEdit(self.block.label.toPlainText())
        self.setWindowIcon(QIcon(ventil.pixmap()))
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        self.hFlipBoxLabel = QLabel("Horizontal Flip")
        self.vFlipBoxLabel = QLabel("Vertical Flip")
        self.complexDivLabel = QLabel("Tempering valve")
        self.hFlipBox = QCheckBox()
        self.vFlipBox = QCheckBox()
        self.complexDiv = QCheckBox()

        self.vFlipBox.setTristate(False)
        self.hFlipBox.setTristate(False)
        self.hFlipBox.setCheckState(self.block.flippedH * 2)
        self.vFlipBox.setCheckState(self.block.flippedV * 2)
        self.complexDiv.setTristate(False)
        self.logger.debug("complexdiv is " + str(self.block.isTempering))
        self.complexDiv.setCheckState(self.block.isTempering * 2)

        flipLayout = QHBoxLayout()
        flipLayout.addWidget(self.hFlipBoxLabel)
        flipLayout.addWidget(self.hFlipBox)
        flipLayout.addWidget(self.vFlipBoxLabel)
        flipLayout.addWidget(self.vFlipBox)
        flipLayout.addWidget(self.complexDivLabel)
        flipLayout.addWidget(self.complexDiv)

        textLayout = QHBoxLayout()
        self.warningLabel = QLabel("<b>Selecting tempering valve will always set Valve Position to 0.</b>")
        textLayout.addWidget(self.warningLabel)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        tab1Layout = QGridLayout(self)
        tab1Layout.addWidget(nameLabel, 0, 0)
        tab1Layout.addWidget(self.le, 0, 1)
        tab1Layout.addLayout(flipLayout, 1, 0, 3, 0)
        tab1Layout.addLayout(textLayout, 3, 0, 3, 0)

        positionLayout = QHBoxLayout()
        self.positionMassFlowSolverLabel = QLabel("Valve Position")
        self.positionMassFlowSolver = QDoubleSpinBox()
        self.positionMassFlowSolver.setDecimals(1)
        self.positionMassFlowSolver.setSingleStep(0.1)
        self.positionMassFlowSolver.setProperty("value", self.valvePosition)
        self.positionMassFlowSolver.setRange(0, 1.0)
        self.positionMassFlowSolver.valueChanged.connect(self.positionMassFlowSolverChanged)
        positionLayout.addWidget(self.positionMassFlowSolverLabel)
        positionLayout.addWidget(self.positionMassFlowSolver)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        # Add tabs
        self.tabs.addTab(self.tab1, "Diagram")
        self.tabs.addTab(self.tab2, "Mass Flow Solver")
        self.tab1.setLayout(tab1Layout)
        self.tab2.setLayout(positionLayout)
        # self.tab2 = layout
        # self.tabs.resize(300, 200)

        # self.tabs.addTab(self.tab2, "Tab 2")
        self.layout2 = QGridLayout(self)
        self.layout2.addWidget(self.tabs, 0, 0)
        self.layout2.addLayout(buttonLayout, 2, 0, 3, 0)
        self.setLayout(self.layout2)

        self.setFixedSize(400, 180)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.hFlipBox.stateChanged.connect(self.setNewFlipStateH)
        self.vFlipBox.stateChanged.connect(self.setNewFlipStateV)
        self.complexDiv.stateChanged.connect(self.setNewComplexState)
        self.setWindowTitle("Properties")
        self.show()

    def acceptedEdit(self):
        self.logger.debug("Changing displayName")
        newName = self.le.text()
        if self.block.isTempering:
            self.block.setPositionForMassFlowSolver(0.0)
            self.block.posLabel.setPlainText(str(self.block.positionForMassFlowSolver))
        if newName.lower() == str(self.block.displayName).lower():
            self.block.posLabel.setPlainText(str(self.block.positionForMassFlowSolver))
            self.close()
        elif newName != "" and not self.nameExists(newName) and newName != self.block.displayName:
            # self.block.setName(newName)
            self.block.label.setPlainText(newName)
            self.block.displayName = newName
            self.block.posLabel.setPlainText(str(self.block.positionForMassFlowSolver))
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

    def setNewComplexState(self, state):
        self.block.setComplexDiv(state)
        self.block.posLabel.setPlainText(str(self.block.positionForMassFlowSolver))

    def positionMassFlowSolverChanged(self, value):
        if self.block.isTempering:
            self.block.setPositionForMassFlowSolver(0.0)
        else:
            self.block.setPositionForMassFlowSolver(value)

    def cancel(self):
        self.close()

    def nameExists(self, n):
        for t in self.parent().trnsysObj:
            if str(t.displayName).lower() == n.lower():
                return True
        return False
