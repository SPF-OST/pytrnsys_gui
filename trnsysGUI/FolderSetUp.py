# pylint: skip-file
# type: ignore

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox, QFileDialog


class FolderSetUp(QDialog):
    """
    A dialog box lets the user choose the path and the name of folder for a new project
    """

    def __init__(self, parent=None):

        super(FolderSetUp, self).__init__(parent)

        self.projectPath = ""
        self.folderName = ""

        projectPathLabel = QLabel("Path to the project folder:")
        self.line1 = QLineEdit()

        folderNameLabel = QLabel("Name of the project folder:")
        self.line2 = QLineEdit()

        self.setProjectPathButton = QPushButton("Set")

        self.setProjectPathButton.setFixedWidth(100)

        projectPathLayout = QHBoxLayout()
        projectPathLayout.addWidget(projectPathLabel)
        projectPathLayout.addWidget(self.line1)
        projectPathLayout.addWidget(self.setProjectPathButton)

        folderNameLayout = QHBoxLayout()
        folderNameLayout.addWidget(folderNameLabel)
        folderNameLayout.addWidget(self.line2)

        self.okButton = QPushButton("Done")
        self.okButton.setFixedWidth(50)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton, alignment=Qt.AlignCenter)

        overallLayout = QVBoxLayout()
        overallLayout.addLayout(projectPathLayout)
        overallLayout.addLayout(folderNameLayout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(800)

        self.okButton.clicked.connect(self.doneEdit)
        self.setProjectPathButton.clicked.connect(self.setProjectPath)
        self.setWindowTitle("New Project")
        self.exec()

    def doneEdit(self):

        self.projectPathFlag = False
        self.folderNameFlag = False
        self.overwriteFolder = True

        self.folderName = self.line2.text()

        if self.projectPath == "":
            msgBox = QMessageBox()
            msgBox.setText("Please set the path to the project folder.")
            msgBox.exec()
        else:
            self.projectPathFlag = True

        if self.folderName == "":
            msgBox = QMessageBox()
            msgBox.setText("Please define the name of the project folder.")
            msgBox.exec()
        else:
            self.folderNameFlag = True

        self.projectFolder = os.path.join(self.projectPath.replace("/", "\\"), self.folderName)

        if os.path.isdir(self.projectFolder):

            qmb = QMessageBox()
            qmb.setText("This project folder already exists. Overwrite?")
            qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            qmb.setDefaultButton(QMessageBox.No)
            ret = qmb.exec()

            if ret == QMessageBox.No:
                self.overwriteFolder = False

        if self.projectPathFlag and self.folderNameFlag and self.overwriteFolder:
            self.close()

    def cancel(self):
        self.close()

    def setProjectPath(self):
        """
        Path to the project file as user input by choosing an existing directory
        """
        self.projectPath = str(QFileDialog.getExistingDirectory(self, "Select Project Path"))
        if self.projectPath != "":
            self.line1.setText(self.projectPath)
        pass
