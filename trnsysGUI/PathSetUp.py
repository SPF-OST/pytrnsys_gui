from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout, QGridLayout, QTabWidget, \
    QVBoxLayout, QWidget, QDoubleSpinBox, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon


class PathSetUp(QDialog):

    def __init__(self, parent=None):
        super(PathSetUp, self).__init__(parent)

        self.currentExportPath, self.currentDiagramPath = self.getCurrentPaths()
        self.exportPath = ''
        self.diagramPath = ''

        exportPathLabel = QLabel("Export Path:")
        self.le = QLineEdit(self.currentExportPath)
        self.le.setDisabled(True)

        diagramPathLabel = QLabel("Diagram Path:")
        self.le2 = QLineEdit(self.currentDiagramPath)
        self.le2.setDisabled(True)

        self.setExportPathButton = QPushButton("Set Export Path")
        self.setDiagramPathButton = QPushButton("Set Diagram Path")
        self.setExportPathButton.setFixedWidth(100)
        self.setDiagramPathButton.setFixedWidth(100)

        exportLayout = QHBoxLayout()
        exportLayout.addWidget(exportPathLabel)
        exportLayout.addWidget(self.le)
        exportLayout.addWidget(self.setExportPathButton)

        diagramLayout = QHBoxLayout()
        diagramLayout.addWidget(diagramPathLabel)
        diagramLayout.addWidget(self.le2)
        diagramLayout.addWidget(self.setDiagramPathButton)

        self.okButton = QPushButton("Done")
        self.okButton.setFixedWidth(50)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton, alignment=Qt.AlignCenter)

        overallLayout = QVBoxLayout()
        overallLayout.addLayout(exportLayout)
        overallLayout.addLayout(diagramLayout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(800)

        self.okButton.clicked.connect(self.doneEdit)
        self.setExportPathButton.clicked.connect(self.setExportPath)
        self.setDiagramPathButton.clicked.connect(self.setDiagramPath)
        self.setWindowTitle("Set Paths")
        self.show()

    def doneEdit(self):
        """
        Saves the paths into filepath.txt
        """
        if self.exportPath == '' and self.diagramPath == '':
            if self.currentExportPath == 'None' and self.currentDiagramPath == 'None':
                msgBox = QMessageBox()
                msgBox.setText("Please set both paths!")
                msgBox.exec()
            elif self.currentExportPath == 'None':
                msgBox = QMessageBox()
                msgBox.setText("Please set export path!")
                msgBox.exec()
            elif self.currentDiagramPath == 'None':
                msgBox = QMessageBox()
                msgBox.setText("Please set diagram path!")
                msgBox.exec()
            else:
                self.close()
        elif self.exportPath == '':
            if self.currentExportPath == 'None':
                msgBox = QMessageBox()
                msgBox.setText("Please set export path!")
                msgBox.exec()
            else:
                self.writeIntoFile(self.exportPath, self.diagramPath)
                self.close()
        elif self.diagramPath == '':
            if self.currentDiagramPath == 'None':
                msgBox = QMessageBox()
                msgBox.setText("Please set diagram path!")
                msgBox.exec()
            else:
                self.writeIntoFile(self.exportPath, self.diagramPath)
                self.close()
        else:
            self.writeIntoFile(self.exportPath, self.diagramPath)
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

    def getCurrentPaths(self):
        """
        read from filepath.txt to get current paths.
        returns export path and diagram path.
        """
        return "path1", "None"
        pass

    def writeIntoFile(self, string1, string2):
        exportPathStr = "Export:"
        diagramPathStr = "Diagram:"
        if string1 != '':
            exportPathStr = exportPathStr + string1
        if string2 != '':
            diagramPathStr = diagramPathStr + string2
        print(exportPathStr, diagramPathStr)
        pass
