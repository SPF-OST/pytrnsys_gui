# pylint: disable=invalid-name

import pathlib as _pl

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QGridLayout,
    QMessageBox,
    QFileDialog,
)

import trnsysGUI.BlockItem as _bi


class BlockDlg(QDialog):  # pylint: disable=too-many-instance-attributes
    def __init__(self, block: _bi.BlockItem, parent=None):
        super().__init__(parent)
        nameLabel = QLabel("Name:")
        self.logger = parent.logger
        self.block = block
        self.lineEdit = QLineEdit(self.block.label.toPlainText())
        self.setWindowIcon(QIcon(block.pixmap()))
        self.loadButton = QPushButton("Load")
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
        buttonLayout.addWidget(self.loadButton)
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.lineEdit, 0, 1)
        layout.addLayout(flipLayout, 1, 0, 2, 0)
        layout.addLayout(buttonLayout, 2, 0, 2, 0)
        self.setLayout(layout)

        self.setFixedSize(300, 150)

        self.loadButton.clicked.connect(self.loadFile)
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.hFlipBox.stateChanged.connect(self.setNewFlipStateH)
        self.vFlipBox.stateChanged.connect(self.setNewFlipStateV)
        self.setWindowTitle("Properties")
        self.loadButton.setDisabled(True)
        self.disableLoad()
        self.show()

    def acceptedEdit(self):
        self.logger.debug("Changing displayName")
        newName = self.lineEdit.text()
        if newName.lower() == str(self.block.displayName).lower():
            self.close()
        elif newName == "":
            msgb = QMessageBox()
            msgb.setText("Please Enter a name!")
            msgb.exec()
        elif self._nameExists(newName) or self._nameExistsInDdckFolder(newName):
            msgb = QMessageBox()
            msgb.setText("Name already exist!")
            msgb.exec()
        else:
            self.block.setName(newName)
            self.close()

    def setNewFlipStateH(self, state):
        self.block.updateFlipStateH(state)
        self.block.updateSidesFlippedH()

    def setNewFlipStateV(self, state):
        self.block.updateFlipStateV(state)
        self.block.updateSidesFlippedV()

    def cancel(self):
        self.close()

    def _nameExists(self, name):
        for item in self.parent().trnsysObj:
            if str(item.displayName).lower() == name.lower():
                return True
        return False

    def _nameExistsInDdckFolder(self, name):
        projectFolderDdckPath = _pl.Path(self.parent().projectFolder + "\\ddck")
        projectDdckFiles = list(projectFolderDdckPath.iterdir())
        for file in projectDdckFiles:
            if file.name.lower() == name.lower():
                return True
        return False

    # unused
    def loadFile(self):
        self.logger.debug("Opening diagram")
        fileName = QFileDialog.getOpenFileName(self, "Open diagram", filter="*.ddck")[0]
        if fileName != "":
            if len(self.block.propertyFile) < 2:
                self.block.propertyFile.append(fileName)
            else:
                self.block.propertyFile.clear()
                self.block.propertyFile.append(fileName)
        else:
            self.logger.debug("No filename chosen")

    def disableLoad(self):
        if self.block.name in ("TeePiece", "WTap_main"):
            self.loadButton.setDisabled(True)
