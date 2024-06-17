# pylint: skip-file
# type: ignore

import pathlib as _pl

from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QDoubleSpinBox
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QWidget

import trnsysGUI.TVentil as _vnt
import trnsysGUI.names.dialog as _ndialog
import trnsysGUI.names.rename as _rename


class TVentilDlg(_ndialog.ChangeNameDialogBase):
    def __init__(self, ventil: _vnt.TVentil, renameHelper: _rename.RenameHelper, projectFolder: str) -> None:
        super().__init__(ventil, renameHelper, _pl.Path(projectFolder))

        self._blockItem = ventil
        self.valvePosition = self._blockItem.positionForMassFlowSolver
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
        self.hFlipBox.setCheckState(self._blockItem.flippedH * 2)
        self.vFlipBox.setCheckState(self._blockItem.flippedV * 2)
        self.complexDiv.setTristate(False)
        self.complexDiv.setCheckState(self._blockItem.isTempering * 2)

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
        nameLabel = QLabel("Name:")
        tab1Layout.addWidget(nameLabel, 0, 0)
        tab1Layout.addWidget(self._displayNameLineEdit, 0, 1)
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

    def setNewFlipStateH(self, state):
        self._blockItem.updateFlipStateH(state)
        self._blockItem.updateSidesFlippedH()

    def setNewFlipStateV(self, state):
        self._blockItem.updateFlipStateV(state)
        self._blockItem.updateSidesFlippedV()

    def setNewComplexState(self, state):
        self._blockItem.setComplexDiv(state)
        self._blockItem.posLabel.setPlainText(str(self._blockItem.positionForMassFlowSolver))

    def positionMassFlowSolverChanged(self, value):
        if self._blockItem.isTempering:
            self._blockItem.setPositionForMassFlowSolver(0.0)
        else:
            self._blockItem.setPositionForMassFlowSolver(value)

    def cancel(self):
        self.close()
