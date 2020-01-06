from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout, QGridLayout


class TVentilDlg(QDialog):
    def __init__(self, block, parent=None):
        super(TVentilDlg, self).__init__(parent)
        nameLabel = QLabel("Name:")
        self.block = block
        self.le = QLineEdit(self.block.label.toPlainText())

        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        self.hFlipBoxLabel = QLabel("Horizontal Flip")
        self.vFlipBoxLabel = QLabel("Vertical Flip")
        self.complexDivLabel = QLabel("Set complex")
        self.hFlipBox = QCheckBox()
        self.vFlipBox = QCheckBox()
        self.complexDiv = QCheckBox()

        self.vFlipBox.setTristate(False)
        self.hFlipBox.setTristate(False)
        self.hFlipBox.setCheckState(self.block.flippedH * 2)
        self.vFlipBox.setCheckState(self.block.flippedV * 2)
        self.complexDiv.setTristate(False)
        self.complexDiv.setCheckState(self.block.isComplexDiv)

        flipLayout = QHBoxLayout()
        flipLayout.addWidget(self.hFlipBoxLabel)
        flipLayout.addWidget(self.hFlipBox)
        flipLayout.addWidget(self.vFlipBoxLabel)
        flipLayout.addWidget(self.vFlipBox)
        flipLayout.addWidget(self.complexDivLabel)
        flipLayout.addWidget(self.complexDiv)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(flipLayout, 1, 0, 3, 0)
        layout.addLayout(buttonLayout, 2, 0, 3, 0)
        self.setLayout(layout)

        self.setFixedSize(300, 150)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.hFlipBox.stateChanged.connect(self.setNewFlipStateH)
        self.vFlipBox.stateChanged.connect(self.setNewFlipStateV)
        self.complexDiv.stateChanged.connect(self.setNewComplexState)
        self.setWindowTitle("Properties")
        self.show()

    def acceptedEdit(self):
        print("Changing displayName")
        newName = self.le.text()
        self.block.label.setPlainText(newName)
        self.block.displayName = newName
        self.close()

    def setNewFlipStateH(self, state):
        self.block.updateFlipStateH(state)

    def setNewFlipStateV(self, state):
        self.block.updateFlipStateV(state)

    def setNewComplexState(self, state):
        self.block.setComplexDiv(state)

    def cancel(self):
        self.close()
