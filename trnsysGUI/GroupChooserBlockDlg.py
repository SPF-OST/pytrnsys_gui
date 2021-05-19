# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QListWidget, QHBoxLayout, QVBoxLayout


class GroupChooserBlockDlg(QDialog):
    def __init__(self, block, parent=None):
        super(GroupChooserBlockDlg, self).__init__(parent)
        headerLabel = QLabel("Pick a group for this block:")
        self.block = block

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
        for g in self.block.parent.parent().groupList:
            self.listw.addItem(g.displayName)

    def acceptedEdit(self):
        if len(self.listw.selectedItems()) > 0:
            self.block.setBlockToGroup(self.listw.selectedItems()[0].text())
            self.close()

    def cancel(self):
        # print("Canceling")
        self.close()

    # def removeHxL(self):
    #     for i in self.storage.heatExchangers:
    #         # Name is identified through index of comma
    #         for j in self.listWL.selectedItems():
    #             if i.displayName == j.text()[:j.text().find(",")]:
    #                 self.storage.heatExchangers.remove(i)
    #                 self.listWL.takeItem(self.listWL.row(self.listWL.selectedItems()[0]))
    #                 self.storage.parent.scene().removeItem(i.port1)
    #                 self.storage.parent.scene().removeItem(i.port2)
    #                 self.storage.parent.scene().removeItem(i)
