# pylint: skip-file
# type: ignore

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QGridLayout,
    QMessageBox,
    QFileDialog,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt5.QtGui import QColor


class FileOrderingDialog(QDialog):
    def __init__(self, fileList, parent=None):
        super(FileOrderingDialog, self).__init__(parent)
        self.fileList = fileList
        self.names = []
        layout = QVBoxLayout()

        self.table = QTableWidget(len(fileList), 2)
        self.table.setMinimumSize(800, 200)
        self.table.setColumnWidth(0, 700)
        self.table.setHorizontalHeaderItem(0, QTableWidgetItem("File"))
        self.table.setHorizontalHeaderItem(1, QTableWidgetItem("Priority"))

        for i in range(0, len(self.fileList)):
            item = QTableWidgetItem(self.fileList[i])
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(i, 0, item)

        self.tipText = QLabel("Input 0 to omit from run.config")
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.tipText)
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addWidget(self.table)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

        self.changed_items = []
        # self.table.itemChanged.connect(self.log_change)

        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)
        self.setWindowTitle("Set Priority")
        self.show()

    def acceptedEdit(self):
        print("Accepting")
        self.getUserInputs()
        msgb = QMessageBox()

        if not self.checkAllAreIntegers(self.changed_items):
            msgb.setText("Invalid input!")
            msgb.exec_()
            return

        if not self.checkListlength(self.changed_items, self.fileList):
            msgb.setText("Invalid inputs!")
            msgb.exec_()
            return

        self.customSortPaths()
        self.updateConfig()
        self.close()

    def cancel(self):
        self.close()

    def getUserInputs(self):
        self.changed_items.clear()
        for i in range(0, self.table.rowCount()):
            data = self.table.item(i, 1)
            if not data == None and not data == "":
                self.changed_items.append(data.text())

    def customSortPaths(self):
        self.sortedPaths = [x for _, x in sorted(zip(self.changed_items, self.fileList))]
        self.deleteUnwanted()
        print(self.sortedPaths)

    def deleteUnwanted(self):
        zeroCounts = 0
        print("self.changeditems:", self.changed_items)
        for value in self.changed_items:
            if int(value) == 0:
                zeroCounts += 1
        self.finalPathList = self.sortedPaths[zeroCounts:]

    def updateConfig(self):
        config = self.parent().configToEdit

        with open(config, "r") as file:
            lines = file.readlines()
            lines.append("\n")

        header = "LOCAL$ generic\head.ddck\n"
        end = "LOCAL$ generic\end.ddck"

        lines.append(header)
        for items in self.finalPathList:
            item = items.replace("/", "\\")
            item = item.split("ddck\\")[-1]
            print("Item:", item)
            stringToAppend = item
            print(stringToAppend)
            lines.append("LOCAL$ " + stringToAppend + "\n")
        lines.append(end)

        with open(config, "w") as file:
            file.writelines(lines)

    def checkAllAreIntegers(self, list):
        for items in list:
            if not items.isdigit():
                return False
        return True

    def checkListlength(self, list1, list2):
        if len(list1) == len(list2):
            return True
        else:
            return False

    # def log_change(self, item):
    #     self.table.blockSignals(True)
    #     item.setBackground(QColor("red"))
    #     self.table.blockSignals(False)
    #     self.changed_items.append(item)
    #     print(item.text(), item.column(), item.row())
    #
    # def update(self):
    #     print("Updating ")
    #     for item in self.changed_items:
    #         self.table.blockSignals(True)
    #         item.setBackground(QColor("red"))
    #         self.table.blockSignals(False)
    #         self.writeToDatabase(item)
    #
    # def writeToDatabase(self, item):
    #     text, col, row = item.text(), item.column(), item.row()
