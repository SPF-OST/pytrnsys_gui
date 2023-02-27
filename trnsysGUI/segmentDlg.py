# pylint: skip-file
# type: ignore

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res
import trnsysGUI.componentAndPipeNameValidator as _cpn
import trnsysGUI.errors as _err


# todo: make upper case
class segmentDlg(_qtw.QDialog):
    def __init__(self, seg, parent):
        super(segmentDlg, self).__init__(parent)
        self.seg = seg
        nameLabel = _qtw.QLabel("Name:")
        self.le = _qtw.QLineEdit(self.seg.connection.displayName)

        self.okButton = _qtw.QPushButton("OK")
        self.cancelButton = _qtw.QPushButton("Cancel")

        buttonLayout = _qtw.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = _qtw.QGridLayout()
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
        result = nameValidator.validateName(newName)
        if _res.isError(result):
            errorMessage = _res.error(result)
            _err.showErrorMessageBox(errorMessage.message)
            return

        self.applyNameChange(newName)
        self.close()

    def applyNameChange(self, newName):
        self.seg.connection.setDisplayName(newName)
        for segment in self.seg.connection.segments:
            segment.setToolTip(newName)

    def isOldName(self, name):
        return name.lower() == str(self.seg.connection.displayName).lower()

    def cancel(self):
        self.close()

    def getExistingNames(self):
        existingNames = [str(t.displayName) for t in self.parent().trnsysObj]
        return existingNames
