# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout, QDialog, QMessageBox

import trnsysGUI.componentAndPipeNameValidator as _cpn


# todo: make upper case
class segmentDlg(QDialog):
    def __init__(self, seg, parent):
        super(segmentDlg, self).__init__(parent)
        self.seg = seg
        nameLabel = QLabel("Name:")
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
        # todo: use result class
        if self.isOldName(newName):
            self.close()
            return

        existingNames = self.getExistingNames()
        nameValidator = _cpn.ComponentAndPipeNameValidator(existingNames)
        errorMessage = nameValidator.validateName(newName)
        if errorMessage:
            self.respondInMessageBoxWith(errorMessage)
            return

        self.applyNameChange(newName)
        self.close()

    def applyNameChange(self, newName):
        self.seg.connection.setDisplayName(newName)
        for segment in self.seg.connection.segments:
            segment.setToolTip(newName)

    def isOldName(self, name):
        return name.lower() == str(self.seg.connection.displayName).lower()

    @staticmethod
    def respondInMessageBoxWith(response):
        msgb = QMessageBox()
        msgb.setText(response)
        msgb.exec()

    def cancel(self):
        self.close()

    def getExistingNames(self):
        existingNames = [str(t.displayName) for t in self.parent().trnsysObj]
        return existingNames
