import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout, QGridLayout, QTabWidget, \
    QVBoxLayout, QWidget, QDoubleSpinBox, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon


class PathSetUp(QDialog):

    def __init__(self, parent=None):
        super(PathSetUp, self).__init__(parent)

        self.currentExportPath, self.currentDiagramPath, self.currentDdckPath = self.getCurrentPaths()
        self.exportPath = ''
        self.diagramPath = ''
        self.ddckPath = ''

        exportPathLabel = QLabel("Export Path:")
        self.le = QLineEdit(self.currentExportPath)
        self.le.setDisabled(True)

        diagramPathLabel = QLabel("Diagram Path:")
        self.le2 = QLineEdit(self.currentDiagramPath)
        self.le2.setDisabled(True)

        ddckPathLabel = QLabel("ddck Path:")
        self.le3 = QLineEdit(self.currentDdckPath)
        self.le3.setDisabled(True)

        self.setExportPathButton = QPushButton("Set Export Path")
        self.setDiagramPathButton = QPushButton("Set Diagram Path")
        self.setDdckPathButton = QPushButton("Set ddck Path")
        self.setExportPathButton.setFixedWidth(100)
        self.setDiagramPathButton.setFixedWidth(100)
        self.setDdckPathButton.setFixedWidth(100)

        exportLayout = QHBoxLayout()
        exportLayout.addWidget(exportPathLabel)
        exportLayout.addWidget(self.le)
        exportLayout.addWidget(self.setExportPathButton)

        diagramLayout = QHBoxLayout()
        diagramLayout.addWidget(diagramPathLabel)
        diagramLayout.addWidget(self.le2)
        diagramLayout.addWidget(self.setDiagramPathButton)

        ddckLayout = QHBoxLayout()
        ddckLayout.addWidget(ddckPathLabel)
        ddckLayout.addWidget(self.le3)
        ddckLayout.addWidget(self.setDdckPathButton)

        self.okButton = QPushButton("Done")
        self.okButton.setFixedWidth(50)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton, alignment=Qt.AlignCenter)

        overallLayout = QVBoxLayout()
        overallLayout.addLayout(exportLayout)
        overallLayout.addLayout(diagramLayout)
        overallLayout.addLayout(ddckLayout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(800)

        self.okButton.clicked.connect(self.doneEdit)
        self.setExportPathButton.clicked.connect(self.setExportPath)
        self.setDiagramPathButton.clicked.connect(self.setDiagramPath)
        self.setDdckPathButton.clicked.connect(self.setDdckPath)
        self.setWindowTitle("Set Paths")
        self.show()

    def doneEdit(self):
        """
        Saves the paths into filepath.txt
        """
        self.exportFlag = False
        self.diagramFlag = False
        self.ddckFlag = False

        # if self.exportPath == '' and self.diagramPath == '':
        #     if self.currentExportPath == 'None' or self.currentDiagramPath == 'None':
        #         msgBox = QMessageBox()
        #         msgBox.setText("Please set both paths!")
        #         msgBox.exec()
        #     elif self.currentExportPath == 'None':
        #         msgBox = QMessageBox()
        #         msgBox.setText("Please set export path!")
        #         msgBox.exec()
        #     elif self.currentDiagramPath == 'None':
        #         msgBox = QMessageBox()
        #         msgBox.setText("Please set diagram path!")
        #         msgBox.exec()
        #     else:
        #         self.close()
        # elif self.exportPath == '':
        #     if self.currentExportPath == 'None':
        #         msgBox = QMessageBox()
        #         msgBox.setText("Please set export path!")
        #         msgBox.exec()
        #     else:
        #         self.writeIntoFile(self.exportPath, self.diagramPath)
        #         self.close()
        # elif self.diagramPath == '':
        #     if self.currentDiagramPath == 'None':
        #         msgBox = QMessageBox()
        #         msgBox.setText("Please set diagram path!")
        #         msgBox.exec()
        #     else:
        #         self.writeIntoFile(self.exportPath, self.diagramPath)
        #         self.close()
        # else:
        #     self.writeIntoFile(self.exportPath, self.diagramPath)
        #     self.close()


        if self.exportPath == '':
            if self.currentExportPath == '':
                msgBox = QMessageBox()
                msgBox.setText("Please set export path!")
                msgBox.exec()
            else:
                self.exportFlag = True
        else:
            self.exportFlag = True

        if self.diagramPath == '':
            if self.currentDiagramPath == '':
                msgBox = QMessageBox()
                msgBox.setText("Please set diagram path!")
                msgBox.exec()
            else:
                self.diagramFlag = True
        else:
            self.diagramFlag = True

        if self.ddckPath == '':
            if self.currentDdckPath == '':
                msgBox = QMessageBox()
                msgBox.setText("Please set ddck path!")
                msgBox.exec()
            else:
                self.ddckFlag = True
        else:
            self.ddckFlag = True
        print(self.exportFlag, self.diagramFlag, self.ddckFlag)
        if self.exportFlag and self.diagramFlag and self.ddckFlag:
            self.writeIntoFile(self.exportPath, self.diagramPath, self.ddckPath)
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
        self.ddckPath = str(QFileDialog.getExistingDirectory(self, "Select Ddck Path"))
        if self.ddckPath != '':
            self.le3.setText(self.ddckPath)
        pass

    def getCurrentPaths(self):
        """
        read from filepath.txt to get current paths.
        returns export path and diagram path.
        """
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(ROOT_DIR, 'filepaths')
        exportPath = ''
        diagramPath = ''
        ddckPath = ''
        with open(filepath, 'r') as file:
            data = file.readlines()

        try:
            data[0]
        except IndexError:
            print("Empty file")
        else:
            exportPath = data[0]

        try:
            data[1]
        except IndexError:
            print("Empty file")
        else:
            diagramPath = data[1]

        try:
            data[2]
        except IndexError:
            print("Empty file")
        else:
            ddckPath = data[2]

        return exportPath, diagramPath, ddckPath

    def writeIntoFile(self, string1, string2, string3):
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(ROOT_DIR, 'filepaths')
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
        if string3 != '':
            try:
                data[2]
            except IndexError:
                data.append(string3 + '\n')
            else:
                data[2] = string3 + '\n'
        print(data)
        with open(filepath, 'w') as file:
            file.writelines(data)
