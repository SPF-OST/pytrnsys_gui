# pylint: skip-file
# type: ignore

from PyQt5.QtWidgets import QLabel, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QDialog


class groupsEditor(QDialog):
    def __init__(self, parent):
        super(groupsEditor, self).__init__(parent)
        self.diag = parent
        nameLabel = QLabel("Edit groups:")

        VLayout = QVBoxLayout()
        VLayout.addWidget(nameLabel)
        self.listW = QListWidget()
        self.listVGroups = QListWidget()
        self.listVGProps = QListWidget()

        VLayout.addWidget(self.listW)
        VLayout.addWidget(self.listVGroups)
        VLayout.addWidget(self.listVGProps)

        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)

        VLayout.addLayout(buttonLayout)
        self.setLayout(VLayout)

        self.listW.itemSelectionChanged.connect(self.groupSelected)
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Group properties")

        self.loadGroups()
        self.loadProps("defaultGroup")

        self.show()

    def groupSelected(self):
        self.loadGroupItems(self.listW.selectedItems()[0].text())
        self.loadProps(self.listW.selectedItems()[0].text())

    def loadGroupItems(self, name):
        self.removeGroupItems()
        for g in self.diag.groupList:
            if g.displayName == name:
                for it in g.itemList:
                    self.listVGroups.addItem(it.displayName)

    def removeGroupItems(self):
        self.listVGroups.clear()

    def loadProps(self, name):
        self.removeGroupProps()
        for g in self.diag.groupList:
            if g.displayName == name:
                self.listVGProps.addItem(str(g.exportDi))
                self.listVGProps.addItem(str(g.exportU))
                self.listVGProps.addItem(str(g.exportL))

    def removeGroupProps(self):
        self.listVGProps.clear()

    def loadGroups(self):
        for g in self.diag.groupList:
            self.listW.addItem(g.displayName)

    def acceptedEdit(self):
        self.close()

    def cancel(self):
        self.close()
