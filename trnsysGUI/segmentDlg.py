# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout, QDialog, QMessageBox


class segmentDlg(QDialog):
    def __init__(self, seg, parent=None):
        super(segmentDlg, self).__init__(parent)
        self.seg = seg
        nameLabel = QLabel("Name:")
        objectLabel = QLabel("Object:" + str(self.seg))
        self.le = QLineEdit(self.seg.parent.displayName)

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
        # print("Changing displayName")
        newName = self.le.text()
        if newName.lower() == str(self.seg.parent.displayName).lower():
            self.close()
        elif newName != "" and not self.nameExists(newName):
            self.seg.parent.setDisplayName(newName)
            for segment in self.seg.parent.segments:
                segment.setToolTip(newName)
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
