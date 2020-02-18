from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QLabel, QLineEdit, QGridLayout, QHBoxLayout, QListWidget, QPushButton, QSpacerItem, \
    QVBoxLayout, QRadioButton, QDialog, QTabWidget, QWidget


class DifferenceDlg(QDialog):
    def __init__(self, parent, exportList, referenceList):
        super(DifferenceDlg, self).__init__(parent)
        self.parent = parent

        spacerHeight = 15


        self.tabs = QTabWidget()
        self.tab1 = QWidget()

        self.tabs.addTab(self.tab1, "Differences")

        description = QLabel("The differences between the files:")

        g1 = QGridLayout()
        reasonLabel = QLabel("<b>Reason <b>")
        g1.addWidget(reasonLabel, 0, 0, 1, 2)

        qhbL = QHBoxLayout()

        self.listWL = QListWidget()
        for items in exportList:
            self.listWL.addItem(items)
        qhbL.addWidget(self.listWL)

        self.listWR = QListWidget()
        for items in referenceList:
            self.listWR.addItem(items)
        qhbL.addWidget(self.listWR)

        promptLabel = QLabel("Please state reason for change.")
        inputLabel = QLabel("Input reason here:")
        self.reasonInput = QLineEdit("Input reason here")

        changeButton = QPushButton("Change")
        changeButton.clicked.connect(self.acceptChange)
        ignoreButton = QPushButton("Ignore")
        ignoreButton.clicked.connect(self.ignoreChange)

        g1.addWidget(promptLabel, 1, 0, 1, 1)
        g1.addWidget(inputLabel, 2, 0, 1, 1)
        g1.addWidget(self.reasonInput, 3, 0, 1, 3)
        g1.addWidget(changeButton, 4, 0, 1, 1)
        g1.addWidget(ignoreButton, 4, 2, 1, 1)
        spaceHx = QSpacerItem(self.width(), spacerHeight)
        g1.addItem(spaceHx, 5, 0, 1, 2)

        self.okButton = QPushButton("Ok")
        self.cancelButton = QPushButton("Cancel")
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)

        l = QVBoxLayout()
        l.addWidget(description)
        l.addWidget(reasonLabel)

        t1Layout = QVBoxLayout()
        t1Layout.addLayout(qhbL)
        t1Layout.addLayout(g1)

        self.tab1.setLayout(t1Layout)

        l.addWidget(self.tabs)
        l.addWidget(self.okButton)
        l.addWidget(self.cancelButton)

        self.setLayout(l)
        self.setFixedSize(1000, 1000)

        self.listWR.setSelectionMode(1)
        self.listWL.setSelectionMode(1)
        self.listWR.clicked.connect(self.listWRClicked)
        self.listWL.clicked.connect(self.listWLClicked)

        self.exec_()

    def listWLClicked(self):
        self.listWR.clearSelection()

    def listWRClicked(self):
        self.listWL.clearSelection()

    def acceptChange(self):
        pass

    def ignoreChange(self):
        pass

    def acceptedEdit(self):
        self.close()

    def cancel(self):
        self.close()


