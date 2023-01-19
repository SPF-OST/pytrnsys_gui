# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout, QDialog, QMessageBox


class respondToUnacceptableNaming:
    def __init__(self, name):
        self.name = name
        self.unAcceptableName = self.nameContainsUnacceptableCharacters(name)
        self.response = self.responseToUnacceptableName()

    def nameContainsUnacceptableCharacters(self, name):
        return not name.isalnum()

    def responseToUnacceptableName(self):
        if self.unAcceptableName is True:
            return "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                   "Please use only letters and numbers."


class segmentDlg(QDialog):
    def __init__(self, seg, parent=None):
        super(segmentDlg, self).__init__(parent)
        self.seg = seg
        nameLabel = QLabel("Name:")
        objectLabel = QLabel("Object:" + str(self.seg))
        self.le = QLineEdit(self.seg.connection.displayName)

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
        # layout.addWidget(objectLabel, 3, 0, 1, 2)  # Only for debug (Why do I need a 3 here instead of a 2 for int:row?)
        self.setLayout(layout)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Change connection name")
        self.show()

    def acceptedEdit(self):
        newName = self.le.text()
        if newName.lower() == str(self.seg.connection.displayName).lower():
            self.close()
        elif self.nameContainsUnacceptableCharacters(newName):
            response = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                       "Please use only letters and numbers."
            self.respondInMessageBoxWith(response)
        elif newName != "" and not self.nameExists(newName):
            self.seg.connection.setDisplayName(newName)
            for segment in self.seg.connection.segments:
                segment.setToolTip(newName)
            self.close()
        elif newName == "":
            self.respondInMessageBoxWith("Please Enter a name!")
        elif self.nameExists(newName):
            self.respondInMessageBoxWith("Name already exist!")

    def respondInMessageBoxWith(self, response):
        msgb = QMessageBox()
        msgb.setText(response)
        msgb.exec()

    def cancel(self):
        self.close()

    def nameExists(self, n):
        for t in self.parent().trnsysObj:
            if str(t.displayName).lower() == n.lower():
                return True
        return False

    def nameContainsUnacceptableCharacters(self, name):
        return not name.isalnum()

