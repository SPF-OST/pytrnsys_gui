# pylint: skip-file
# type: ignore

import os
from datetime import datetime
import sys

from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
    QGridLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSpacerItem,
    QVBoxLayout,
    QRadioButton,
    QDialog,
    QTabWidget,
    QWidget,
    QMessageBox,
)


class DifferenceDlg(QDialog):
    """
    This is the dialog box that displays the differences between the export
    file and the reference file.

    exportList and referenceList contains the list of unmatched strings from the
    exported file and reference file respectively.

    fileName refers to the name of the file where the differences are found.
    """

    def __init__(self, parent, exportList, referenceList, fileName):
        super(DifferenceDlg, self).__init__(parent)
        self.parent = parent
        self.fileName = fileName
        self.updatedLines = []

        spacerHeight = 15

        self.tabs = QTabWidget()
        self.tab1 = QWidget()

        self.tabs.addTab(self.tab1, "Export vs Reference")

        description = QLabel("The differences between the files: %s" % fileName)

        g1 = QGridLayout()
        reasonLabel = QLabel("<b>Reason <b>")
        g1.addWidget(reasonLabel, 0, 0, 1, 2)

        qhbL = QHBoxLayout()

        self.listWL = QListWidget()
        for items in exportList:
            # splitedString = items.split(':')
            # lineNo = splitedString[0]
            # eString = splitedString[1]
            # rString = 'Line no: ' + lineNo + ', ' + 'Error String: ' + eString
            self.listWL.addItem(items)
        qhbL.addWidget(self.listWL)

        self.listWR = QListWidget()
        for items in referenceList:
            # splitedString = items.split(',')
            # lineNo = splitedString[0]
            # eString = splitedString[1]
            # rString = 'Line no: ' + lineNo + ', ' + 'Error String: ' + eString
            self.listWR.addItem(items)
        qhbL.addWidget(self.listWR)

        promptLabel = QLabel("Please state reason for change.")
        inputLabel = QLabel("Input reason here:")
        self.reasonInput = QLineEdit()
        self.reasonInput.setPlaceholderText("")

        changeButton = QPushButton("Change")
        changeButton.clicked.connect(self.acceptChange)
        changeAllbutton = QPushButton("Change All")
        changeAllbutton.clicked.connect(self.acceptChangeAll)
        # ignoreButton = QPushButton("Ignore")
        # ignoreButton.clicked.connect(self.ignoreChange)

        g1.addWidget(promptLabel, 1, 0, 1, 1)
        g1.addWidget(inputLabel, 2, 0, 1, 1)
        g1.addWidget(self.reasonInput, 3, 0, 1, 3)
        g1.addWidget(changeButton, 4, 0, 1, 1)
        g1.addWidget(changeAllbutton, 4, 2, 1, 1)
        # g1.addWidget(ignoreButton, 4, 2, 1, 1)
        spaceHx = QSpacerItem(self.width(), spacerHeight)
        g1.addItem(spaceHx, 5, 0, 1, 2)

        self.FinishButton = QPushButton("Finish")
        self.FinishButton.clicked.connect(self.finishEdit)

        l = QVBoxLayout()
        l.addWidget(description)
        l.addWidget(reasonLabel)

        t1Layout = QVBoxLayout()
        t1Layout.addLayout(qhbL)
        t1Layout.addLayout(g1)

        self.tab1.setLayout(t1Layout)

        l.addWidget(self.tabs)
        l.addWidget(self.FinishButton)

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
        if len(self.listWR.selectedItems()) > 0:
            msg = QMessageBox()
            msg.setText("Please select from the left side list.")
            msg.exec_()

        if len(self.listWL.selectedItems()) > 0:
            for items in self.listWL.selectedItems():
                # print(items.text()[:items.text().find(":")])
                # print(items.text()[items.text().find(":")+1:])
                lineNo = items.text()[: items.text().find(":")]
                string = items.text()[items.text().find(":") + 1 :]
                self.updatedLines.append(items.text())

        self.updateReferenceFile(lineNo, string)
        self.updateChangelog()
        msg2 = QMessageBox()
        msg2.setText("Changes updated in the reference file.")
        msg2.exec_()

    def acceptChangeAll(self):

        items = []
        lineNoList = []
        stringList = []
        i = 0
        while i < self.listWL.count():
            items.append(self.listWL.item(i))
            i += 1

        for item in items:
            lineNo = item.text()[: item.text().find(":")]
            string = item.text()[item.text().find(":") + 1 :]
            lineNoList.append(lineNo)
            stringList.append(string)
            self.updatedLines.append(item.text())
            # self.updateReferenceFile(lineNo, string)
        self.updateAllChanges(lineNoList, stringList)

        self.updateChangelog()
        msg = QMessageBox()
        msg.setText("All changes updated in the reference file.")
        msg.exec_()

    def finishEdit(self):
        self.close()

    def updateReferenceFile(self, lineNo, string):
        """

        Parameters
        ----------
        lineNo : the line number of the unmatch string
        string : the correct string

        1.Access the reference folder
        2.read from the error file
        3.Update the error lines
        4.write to the error file

        Returns
        -------

        """

        if getattr(sys, "frozen", False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        originalFilePath = os.path.join(ROOT_DIR, "Reference")
        fileToUpdate = os.path.join(originalFilePath, self.fileName)

        with open(fileToUpdate, "r") as file:
            lines = file.readlines()
            # print(lines)

        stringToAdd = string

        try:
            lines[int(lineNo) - 1]
        except IndexError:
            lines.append("")

        lines[int(lineNo) - 1] = stringToAdd

        with open(fileToUpdate, "w") as file:
            file.writelines(lines)

        print("finish running")

    def updateAllChanges(self, lineNoList, stringList):
        """

        Parameters
        ----------
        lineNo : the line number of the unmatch string
        string : the correct string

        1.Access the reference folder
        2.read from the error file
        3.Update the error lines
        4.write to the error file

        Returns
        -------

        """

        if getattr(sys, "frozen", False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        originalFilePath = os.path.join(ROOT_DIR, "Reference")
        fileToUpdate = os.path.join(originalFilePath, self.fileName)

        with open(fileToUpdate, "r") as file:
            lines = file.readlines()

        i = 0
        while i < len(lineNoList):
            try:
                lines[int(lineNoList[i]) - 1]
            except IndexError:
                lines.append("")

            lines[int(lineNoList[i]) - 1] = stringList[i]
            i += 1

        with open(fileToUpdate, "w") as file:
            file.writelines(lines)

        print("finish running")

    def updateChangelog(self):
        linesToAppend = []

        if getattr(sys, "frozen", False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        changelogfile = os.path.join(ROOT_DIR, "changelogs.txt")

        reason = self.reasonInput.text()
        dateAndTime = datetime.now()
        dt_string = dateAndTime.strftime("%d/%m/%Y %H:%M:%S")
        Divider = "==============================================================\n"
        fileName = self.fileName
        updatedLines = self.updatedLines
        reasonHeader = "Reason for change:"
        differenceHeader = "Differences:"
        fileNameHeader = "Name of file:"

        linesToAppend.append(Divider)
        linesToAppend.append(dt_string + "\n" + "\n")
        linesToAppend.append(fileNameHeader + "\n")
        linesToAppend.append(fileName + "\n" + "\n")
        linesToAppend.append(differenceHeader + "\n")
        for lines in updatedLines:
            linesToAppend.append(lines)
        linesToAppend.append("\n" + reasonHeader + "\n")
        linesToAppend.append(reason + "\n")
        linesToAppend.append(Divider)

        with open(changelogfile, "a") as file:
            file.writelines(linesToAppend)
