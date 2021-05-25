# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout


class diagramDlg(QDialog):
    def __init__(self, parent):
        super(diagramDlg, self).__init__(parent)
        self.diag = parent
        nameLabel = QLabel("Diagram name:")
        objectLabel = QLabel("Object:" + str(self.diag))
        self.le = QLineEdit(self.diag.diagramName)

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
        self.setWindowTitle("Diagram Properties")
        self.show()

    def acceptedEdit(self):
        self.diag.renameDiagram(self.le.text())
        self.close()

    def cancel(self):
        self.close()
