import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout, QGridLayout, QTabWidget, \
    QVBoxLayout, QWidget, QDoubleSpinBox, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon


class PathSetUp(QDialog):

    def __init__(self, parent=None):
        """
        A dialog box that allows user to choose the paths for export, diagrams, ddcks and trnsys
        """
        super(PathSetUp, self).__init__(parent)

        # self.currentExportPath, self.currentDiagramPath, self.currentDdckPath, self.currentTrnsysPath = self.getCurrentPaths()
        self.currentDdckPath, self.currentTrnsysPath = self.getCurrentPaths()
        # self.exportPath = ''
        # self.diagramPath = ''
        self.ddckPath = ''
        self.trnsysPath = ''

        # exportPathLabel = QLabel("Export Path:")
        # self.le = QLineEdit(self.currentExportPath)
        # self.le.setDisabled(True)
        #
        # diagramPathLabel = QLabel("Diagram Path:")
        # self.le2 = QLineEdit(self.currentDiagramPath)
        # self.le2.setDisabled(True)

        ddckPathLabel = QLabel("ddck Path:")
        self.le3 = QLineEdit(self.currentDdckPath)
        self.le3.setDisabled(True)

        trnsysPathLabel = QLabel("Trnsys Path:")
        self.le4 = QLineEdit(self.currentTrnsysPath)
        self.le4.setDisabled(True)

        # self.setExportPathButton = QPushButton("Set Export Path")
        # self.setDiagramPathButton = QPushButton("Set Diagram Path")
        self.setDdckPathButton = QPushButton("Set ddck Path")
        self.setTrnsysPathButton = QPushButton("Set Trnsys Path")
        # self.setExportPathButton.setFixedWidth(100)
        # self.setDiagramPathButton.setFixedWidth(100)
        self.setDdckPathButton.setFixedWidth(100)
        self.setTrnsysPathButton.setFixedWidth(100)

        # exportLayout = QHBoxLayout()
        # exportLayout.addWidget(exportPathLabel)
        # exportLayout.addWidget(self.le)
        # exportLayout.addWidget(self.setExportPathButton)
        #
        # diagramLayout = QHBoxLayout()
        # diagramLayout.addWidget(diagramPathLabel)
        # diagramLayout.addWidget(self.le2)
        # diagramLayout.addWidget(self.setDiagramPathButton)

        ddckLayout = QHBoxLayout()
        ddckLayout.addWidget(ddckPathLabel)
        ddckLayout.addWidget(self.le3)
        ddckLayout.addWidget(self.setDdckPathButton)

        trnsysLayout = QHBoxLayout()
        trnsysLayout.addWidget(trnsysPathLabel)
        trnsysLayout.addWidget(self.le4)
        trnsysLayout.addWidget(self.setTrnsysPathButton)

        self.okButton = QPushButton("Done")
        self.okButton.setFixedWidth(50)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton, alignment=Qt.AlignCenter)

        overallLayout = QVBoxLayout()
        # overallLayout.addLayout(exportLayout)
        # overallLayout.addLayout(diagramLayout)
        overallLayout.addLayout(ddckLayout)
        overallLayout.addLayout(trnsysLayout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(800)

        self.okButton.clicked.connect(self.doneEdit)
        # self.setExportPathButton.clicked.connect(self.setExportPath)
        # self.setDiagramPathButton.clicked.connect(self.setDiagramPath)
        self.setDdckPathButton.clicked.connect(self.setDdckPath)
        self.setTrnsysPathButton.clicked.connect(self.setTrnsysPath)
        self.setWindowTitle("Set Paths")
        self.exec()

    def doneEdit(self):
        """
        Saves the paths into filepath.txt
        Checks if any paths is not set, if there are any unset paths, prompt the user to set it by popping up
        error messages.
        Only when all paths are set will it save into filepath.txt
        """
        # self.exportFlag = False
        # self.diagramFlag = False
        self.ddckFlag = False
        self.trnsysFlag = False

        # if self.exportPath == '':
        #     if self.currentExportPath == '':
        #         msgBox = QMessageBox()
        #         msgBox.setText("Please set export path!")
        #         msgBox.exec()
        #     else:
        #         self.exportFlag = True
        # else:
        #     self.exportFlag = True
        #
        # if self.diagramPath == '':
        #     if self.currentDiagramPath == '':
        #         msgBox = QMessageBox()
        #         msgBox.setText("Please set diagram path!")
        #         msgBox.exec()
        #     else:
        #         self.diagramFlag = True
        # else:
        #     self.diagramFlag = True

        if self.ddckPath == '':
            if self.currentDdckPath == '':
                msgBox = QMessageBox()
                msgBox.setText("Please set ddck path!")
                msgBox.exec()
            else:
                self.ddckFlag = True
        else:
            self.ddckFlag = True

        if self.trnsysPath == '':
            if self.currentTrnsysPath == '':
                msgBox = QMessageBox()
                msgBox.setText("Please set Trnsys path!")
                msgBox.exec()
            else:
                self.trnsysFlag = True
        else:
            self.trnsysFlag = True

        # print(self.exportFlag, self.diagramFlag, self.ddckFlag, self.trnsysFlag)
        # if self.exportFlag and self.diagramFlag and self.ddckFlag and self.trnsysFlag:
        #     self.writeIntoFile(self.exportPath, self.diagramPath, self.ddckPath, self.trnsysPath)
        #     self.parent().setTrnsysPath()
        #     self.close()

        print(self.ddckFlag, self.trnsysFlag)
        if self.ddckFlag and self.trnsysFlag:
            self.writeIntoFile(self.ddckPath, self.trnsysPath)
            self.parent().setTrnsysPath()
            self.close()


    def cancel(self):
        self.close()

    def setExportPath(self):
        """
        Lets user choose a directory for exporting
        """
        self.exportPath = str(QFileDialog.getExistingDirectory(self, "Select Export Path"))
        if self.exportPath !='':
            self.le.setText(self.exportPath)
        pass

    def setDiagramPath(self):
        """
        Lets user choose a directory for saving diagrams
        """
        self.diagramPath = str(QFileDialog.getExistingDirectory(self, "Select Diagram Path"))
        if self.diagramPath !='':
            self.le2.setText(self.diagramPath)
        pass

    def setDdckPath(self):
        """
        Lets user choose a directory for exporting ddcks
        """
        self.ddckPath = str(QFileDialog.getExistingDirectory(self, "Select Ddck Path"))
        if self.ddckPath != '':
            self.le3.setText(self.ddckPath)
        pass

    def setTrnsysPath(self):
        """
        Lets user choose the directory when TRNExe.exe is found
        """
        self.trnsysPath = str(QFileDialog.getExistingDirectory(self, "Select Trnsys Path"))
        if self.trnsysPath != '':
            self.le4.setText(self.trnsysPath)
        pass

    def getCurrentPaths(self):
        """
        read from filepath.txt to get current paths.
        returns all the paths.
        """
        print("File:", __file__)
        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)

        # ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        print("root_dir:", ROOT_DIR)
        filepath = os.path.join(ROOT_DIR, 'filepaths.txt')
        # exportPath = ''
        # diagramPath = ''
        ddckPath = ''
        trnsysPath = ''
        with open(filepath, 'r') as file:
            data = file.readlines()

        try:
            data[0]
        except IndexError:
            print("Empty file")
        else:
            # exportPath = data[0]
            ddckPath = data[0]

        try:
            data[1]
        except IndexError:
            print("Empty file")
        else:
            # diagramPath = data[1]
            trnsysPath = data[1]

        # try:
        #     data[2]
        # except IndexError:
        #     print("Empty file")
        # else:
        #     ddckPath = data[2]
        #
        # try:
        #     data[3]
        # except IndexError:
        #     print("Empty file")
        # else:
        #     trnsysPath = data[3]

        # return exportPath, diagramPath, ddckPath, trnsysPath
        return ddckPath, trnsysPath

    def writeIntoFile(self, string1, string2):#, string3, string4):
        """
        Writes to filepath.txt
        Checks if the strings passed in are empty, if not empty, check if filepath contains an existing
        entry for tht string (regardless of it being empty or not). If no, create an entry and append the string
        to that entry. If yes, override the existing entry.
        """
        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        filepath = os.path.join(ROOT_DIR, 'filepaths.txt')
        with open(filepath, 'r') as file:
            data = file.readlines()
        if string1 != '':
            try:
                data[0]
            except IndexError:
                data.append(string1 + '\n')
            else:
                data[0] = string1 + '\n'
        if string2 != '':
            try:
                data[1]
            except IndexError:
                data.append(string2 + '\n')
            else:
                data[1] = string2 + '\n'
        # if string3 != '':
        #     try:
        #         data[2]
        #     except IndexError:
        #         data.append(string3 + '\n')
        #     else:
        #         data[2] = string3 + '\n'
        # if string4 != '':
        #     try:
        #         data[3]
        #     except IndexError:
        #         data.append(string4 + '\n')
        #     else:
        #         data[3] = string4 + '\n'

        print(data)
        with open(filepath, 'w') as file:
            file.writelines(data)
