# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel


class closeDlg(QDialog):
    """
    Not used currently. Keep for future sake.
    Used to prompt user whether to save their current template
    """

    def __init__(self, *args, **kwargs):
        super(closeDlg, self).__init__(*args, **kwargs)

        self.closeBool = False

        self.setWindowTitle("Closing!")
        self.dlgMessage = QLabel()
        self.strMessage = "Do you want to retain the current template for when you next open the application?"
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
        self.closeBool = True
        self.accept()
