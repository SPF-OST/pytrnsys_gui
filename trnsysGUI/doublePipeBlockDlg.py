# pylint: skip-file
# type: ignore

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QGridLayout,
    QMessageBox,
    QFileDialog,
)

import trnsysGUI.BlockItem as _bi


class DoublePipeBlockDlg(QDialog):
    def __init__(self, block: _bi.BlockItem, parent=None):
        super(DoublePipeBlockDlg, self).__init__(parent)
        nameLabel = QLabel("Name:")
        self.logger = parent.logger
        self.block = block
        self.le = QLineEdit(self.block.label.toPlainText())
        self.setWindowIcon(QIcon(block.pixmap()))
        self.loadButton = QPushButton("Load")
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.loadButton)
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(buttonLayout, 2, 0, 2, 0)
        self.setLayout(layout)

        self.setFixedSize(300, 150)

        self.loadButton.clicked.connect(self.loadFile)
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Properties")
        self.loadButton.setDisabled(True)
        self.disableLoad()
        self.show()

    def acceptedEdit(self):
        self.logger.debug("Changing displayName")
        newName = self.le.text()
        if newName.lower() == str(self.block.displayName).lower():
            self.close()
        elif newName != "" and not self.nameExists(newName):
            self.block.setName(newName)
            # self.block.label.setPlainText(newName)
            # self.block.displayName = newName
            self.close()
        elif newName == "":
            msgb = QMessageBox()
            msgb.setText("Please Enter a name!")
            msgb.exec()
        elif self.nameExists(newName):
            msgb = QMessageBox()
            msgb.setText("Name already exist!")
            msgb.exec()

    def cancel(self):
        self.close()

    def nameExists(self, n):
        for t in self.parent().trnsysObj:
            if str(t.displayName).lower() == n.lower():
                return True
        return False

    # unused
    def loadFile(self):
        self.logger.debug("Opening diagram")
        # self.centralWidget.delBlocks()
        fileName = QFileDialog.getOpenFileName(self, "Open diagram", filter="*.ddck")[0]
        if fileName != "":
            if len(self.block.propertyFile) < 2:
                self.block.propertyFile.append(fileName)
            else:
                self.block.propertyFile.clear()
                self.block.propertyFile.append(fileName)
        else:
            self.logger.debug("No filename chosen")
        pass

    def disableLoad(self):
        if self.block.name == "TeePiece" or self.block.name == "WTap_main":
            self.loadButton.setDisabled(True)
