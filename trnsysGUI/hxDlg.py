# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout


class hxDlg(QDialog):
    def __init__(self, hx, sceneparent):
        super(hxDlg, self).__init__(sceneparent)
        self.hx = hx
        nameLabel = QLabel("Name:")
        # objectLabel = QLabel("Object:" + str(self.hx))
        self.le = QLineEdit(self.hx.displayName)

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
        self.setWindowTitle("Change heat exchanger name")
        self.show()

    def acceptedEdit(self):
        self.hx.rename(self.le.text())
        self.close()

    def cancel(self):
        self.close()
