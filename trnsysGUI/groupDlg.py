# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QDialog, QLineEdit, QHBoxLayout, QPushButton, QGridLayout, QLabel


class groupDlg(QDialog):
    def __init__(self, group, parent, itemList):
        super(groupDlg, self).__init__(parent)
        self.setModal(True)
        self.parent = parent
        self.group = group
        self.itemList = itemList
        nameLabel = QLabel("Name:")
        self.le = QLineEdit(self.group.displayName)

        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(buttonLayout, 1, 0, 2, 0)
        self.setLayout(layout)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Set new group")
        self.show()

    def acceptedEdit(self):
        if self.le.text() is not "":
            self.group.setName(self.le.text())
            self.group.setItemsGroup(self.itemList)

            self.parent.selectionMode = False
            self.parent.groupMode = False
            self.close()

    def cancel(self):
        self.parent.selectionMode = False

        self.close()
