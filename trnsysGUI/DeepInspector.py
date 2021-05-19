# pylint: skip-file
# type: ignore

import sys
import re

from PyQt5.QtWidgets import QDialog, QLabel, QHBoxLayout, QPushButton, QLineEdit, QGridLayout, QListWidget, QRadioButton


class DeepInspector(QDialog):
    def __init__(self, parent):
        super(DeepInspector, self).__init__(parent)

        self.stdout = sys.stdout
        self.messages = []

        self.editor = parent
        self.currentObj = parent

        funcLabel = QLabel("Enter function call:")
        self.le = QLineEdit()

        self.okButton = QPushButton("Execute")
        self.cancelButton = QPushButton("Cancel")

        self.listW = QListWidget()

        radioButtonLayout = QHBoxLayout()
        self.rMeth = QRadioButton("Method")
        self.rAttr = QRadioButton("Attr")
        radioButtonLayout.addWidget(self.rMeth)
        radioButtonLayout.addWidget(self.rAttr)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QGridLayout()
        layout.addWidget(funcLabel, 0, 0)
        layout.addWidget(self.le, 1, 0)
        layout.addWidget(self.listW, 2, 0)
        layout.addLayout(radioButtonLayout, 3, 0, 2, 0)
        layout.addLayout(buttonLayout, 5, 0, 2, 0)
        self.setLayout(layout)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Diagram Properties")
        self.show()

    def acceptedEdit(self):
        if not (self.rMeth.isChecked() or self.rAttr.isChecked()):
            print("No button checked")
        else:
            t = self.le.text()
            # b = False
            # if "(" in t:
            #     b = True
            if self.rMeth.isChecked():
                funcStr = re.findall(".{0,}\(", t)[0][:-1]
                argStr = re.findall("\(.{0,}\)", t)[0][1:-1]
                print(funcStr + ", " + argStr)
                if argStr == "":
                    self.executeMeth((funcStr))
                else:
                    self.executeMeth(funcStr, argStr)
            else:
                funcStr = t
                argStr = None
                self.currentObj = self.getAtr(funcStr)

            # self.stopLog()
            print("now in console should appear: " + str(self.messages))
            self.listW.addItem(funcStr)

    def cancel(self):
        self.close()

    def executeMeth(self, meth, *args):
        res = getattr(self.currentObj, meth)(*args)
        # if type(res) is not int and type(res) is not list:
        print(type(res))
        self.currentObj = res

    def getAtr(self, name):
        return getattr(self.currentObj, name)

    def startLog(self):
        sys.stdout = self

    def stopLog(self):
        sys.stdout = self.stdout

    def write(self, text):
        self.messages.append(text)
