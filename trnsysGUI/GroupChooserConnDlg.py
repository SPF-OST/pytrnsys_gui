# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QPushButton, QListWidget, QHBoxLayout, QVBoxLayout, QLabel, QDialog


class GroupChooserConnDlg(QDialog):
    def __init__(self, conn, parent=None):
        super(GroupChooserConnDlg, self).__init__(parent)
        headerLabel = QLabel("Pick a group for this conn:")
        self.conn = conn
        self.parent = parent
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        self.listw = QListWidget()

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)

        vertLayout = QVBoxLayout()
        vertLayout.addWidget(headerLabel)
        vertLayout.addWidget(self.listw)
        vertLayout.addLayout(buttonLayout)

        self.setLayout(vertLayout)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Change group")

        self.loadList()

        self.show()

    def loadList(self):
        for g in self.parent.groupList:
            self.listw.addItem(g.displayName)

    def acceptedEdit(self):
        if len(self.listw.selectedItems()) > 0:
            self.conn.setConnToGroup(self.listw.selectedItems()[0].text())
            self.close()

        # print("Changed group in connDlg to " + str(self.listw.selectedItems()[0].text()))
        # for g in self.parent.groupList:
        #     print(g.displayName)

        self.close()

    def cancel(self):
        # print("Canceling")
        self.close()
