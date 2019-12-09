from PyQt5.QtWidgets import QDialog, QLineEdit, QHBoxLayout, QPushButton, QGridLayout, QLabel


class groupDlg(QDialog):
    def __init__(self, group, parent):
        super(groupDlg, self).__init__(parent)
        self.setModal(True)
        self.parent = parent
        self.group = group
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
        self.setWindowTitle("Change connection name")
        self.show()

    def acceptedEdit(self):
        self.group.setName(self.le.text())
        self.group.setItemsGroup()

        global selectionMode
        selectionMode = False
        self.close()

    def cancel(self):
        global selectionMode
        selectionMode = False

        self.close()

