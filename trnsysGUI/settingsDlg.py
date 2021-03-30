from PyQt5.QtWidgets import QDialog, QLineEdit, QHBoxLayout, QPushButton, QGridLayout, QLabel
from PyQt5 import QtCore


class settingsDlg(QDialog):
    def __init__(self, parent):
        super(settingsDlg, self).__init__(parent)
        self.setModal(True)
        self.parent = parent
        nameLabel = QLabel("Trnsys Exe:")
        self.le = QLineEdit(parent.centralWidget.latexPath)

        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.setColumnMinimumWidth(1, 300)
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(buttonLayout, 1, 0, 2, 0)
        self.setLayout(layout)

        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        self.setWindowTitle("Set new group")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.show()

    def acceptedEdit(self):
        if self.le.text() is not "":
            self.parent.centralWidget.latexPath = self.le.text()
            self.close()

    def cancel(self):
        self.close()
