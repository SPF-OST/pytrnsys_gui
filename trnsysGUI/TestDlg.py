# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel


class TestDlg(QDialog):
    """
    This is the dialog box for testing. It will be called when an exported file cannot be found inside the reference
    folder. (file of same name doesnt exist inside reference folder)
    """

    def __init__(self, exportedFile, *args, **kwargs):
        super(TestDlg, self).__init__(*args, **kwargs)

        self.exportBool = False

        self.setWindowTitle("Error!")
        self.dlgMessage = QLabel()
        self.strMessage = "%s not found inside Reference folder, add the file into Reference folder?" % exportedFile
        self.dlgMessage.setText(self.strMessage)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.acceptExport)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.dlgMessage)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.exec_()

    def acceptExport(self):
        self.exportBool = True
        self.accept()
