# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout, QDialog, QRadioButton


class newPortDlg(QDialog):
    def __init__(self, block, parent=None):
        super(newPortDlg, self).__init__(parent)
        self.block = block
        nameLabel = QLabel("Name:")
        objectLabel = QLabel("Object:" + str(self.block))
        self.le = QLineEdit("0")

        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)

        radioButtonLayout = QHBoxLayout()
        self.oButton = QRadioButton("Output")
        self.iButton = QRadioButton("Input")
        radioButtonLayout.addWidget(self.iButton)
        radioButtonLayout.addWidget(self.oButton)

        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(self.le, 0, 1)
        layout.addLayout(radioButtonLayout, 1, 0, 2, 0)
        layout.addLayout(buttonLayout, 3, 0, 2, 0)
        layout.addWidget(objectLabel, 5, 0, 1, 2)  # Only for debug (Why do I need a 3 here instead of a 2 for int:row?)
        self.setLayout(layout)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Change connection name")
        self.show()

    def acceptedEdit(self):
        if self.le.text() != "":
            height = self.le.text()

            if self.oButton.isChecked():
                io = "o"
            else:
                io = "i"

            self.block.addPort(io, height)

            self.close()

    def cancel(self):
        self.close()
