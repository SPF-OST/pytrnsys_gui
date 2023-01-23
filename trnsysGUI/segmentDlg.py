# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout, QDialog, QMessageBox


class CheckPipeName:
    def __init__(self, name):
        self.name = name
        self.onlyWords = self.removeUnderscores(name)
        self.unacceptableName = self.nameContainsUnacceptableCharacters()
        self.response = self.responseToUnacceptableName()

    def nameContainsUnacceptableCharacters(self):
        if self.containsOnlyNumbers(self.onlyWords):
            return True
        return not self.containsOnlyLettersAndNumbers(self.onlyWords)

    @staticmethod
    def removeUnderscores(name):
        wordsOnly = "".join(list(filter(None, name.split('_'))))
        return wordsOnly

    @staticmethod
    def containsOnlyLettersAndNumbers(string1):
        return string1.isalnum()

    @staticmethod
    def containsOnlyNumbers(string1):
        return string1.isdigit()

    def responseToUnacceptableName(self):
        if self.unacceptableName:
            return "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                   "Please use only letters, numbers, and underscores."


# todo: make upper case
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
        isValidNewName, response = self.checkName(newName)
        if not isValidNewName:
            self.respondInMessageBoxWith(response)
        else:
            if self.nameKept(newName):
                self.close()
            elif not self.nameExists(newName):
                self.seg.connection.setDisplayName(newName)
                for segment in self.seg.connection.segments:
                    segment.setToolTip(newName)
                self.close()

    def checkName(self, newName):
        if newName == "":
            response = "Please Enter a name!"
            self.respondInMessageBoxWith(response)
            return False, response
        elif self.nameContainsUnacceptableCharacters(newName):
            response = "Found unacceptable characters (this includes spaces at the start and the end)\n" \
                       "Please use only letters, numbers, and underscores."
            return False, response
        elif self.nameExists(newName):
            response = "Name already exist!"
            self.respondInMessageBoxWith(response)
            return False, response
        return True, None

    def nameKept(self, name):
        return name.lower() == str(self.seg.connection.displayName).lower()

    @staticmethod
    def respondInMessageBoxWith(response):
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

    @staticmethod
    def nameContainsUnacceptableCharacters(name):
        return CheckPipeName(name).unacceptableName
