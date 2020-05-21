import os
import shutil
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeView, QMenu, QMessageBox, QFileDialog, QInputDialog


class MyQTreeView(QTreeView):
    def __init__(self, model, blockitem):
        """
        Self defined QTreeView that contains operations related to the file explorer
        """
        super(QTreeView, self).__init__()
        self.setContextMenuPolicy(True)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.model = model
        self.item = blockitem

        # for i in range(1, self.model.columnCount()-1):
        #     print('Is column %i hidden : %r' % (i, self.isColumnHidden(i)))
        #     self.hideColumn(i)
        #     print('Is column %i hidden : %r' % (i, self.isColumnHidden(i)))

    def mouseDoubleClickEvent(self, event):
        print("Double clicked")
        self.openFile()

    def mousePressEvent(self,event):
        self.clearSelection()
        QTreeView.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
        menu = QMenu()

        # open = menu.addAction("Open")
        # open.triggered.connect(self.openFile)

        load = menu.addAction("Load")
        load.triggered.connect(self.loadFile)

        dele = menu.addAction("Delete")
        dele.triggered.connect(self.delFile)

        editP = menu.addAction("Edit priority")
        editP.triggered.connect(self.editPriority)

        menu.exec_(event.globalPos())

    def openFile(self):
        """
        When double click on a row, this method is called to open the double clicked file
        """
        print("Opening file")
        filePath = self.getFilePath()
        try:
            if os.path.isfile(filePath):
                os.startfile(filePath)
        except OSError:
            msg = QMessageBox()
            msg.setText("No application is associated with the specified file for this operation")
            msg.exec_()

    def loadFile(self):
        """
        Loads a file into the project path defined by the user.
        Checks if file already exists and allows user to override or cancel the load.
        """
        filePath = self.model.rootPath()
        fileName = QFileDialog.getOpenFileName(self, "Load file", "/Users/parad/OneDrive/Desktop/pytrnsys/pytrnsys/ddck", filter="*.ddck")[0]
        simpFileName = fileName.split('/')[-1]
        loadPath = os.path.join(filePath, simpFileName)
        print(loadPath)
        if fileName != '':
            print("file loaded into %s" % filePath)
            if Path(loadPath).exists():
                qmb = QMessageBox()
                qmb.setText("Warning: " +
                            "A file with the same name exists already. Do you want to overwrite or cancel?")
                qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                qmb.setDefaultButton(QMessageBox.Cancel)
                ret = qmb.exec()
                if ret == QMessageBox.Save:
                    print("Overwriting")
                    # continue
                else:
                    print("Canceling")
                    return
            shutil.copy(fileName, filePath)
            # self.item.parent().centralWidget.fileList.append(filePath)
            try:
                fileList = self.item.parent.parent().fileList
            except AttributeError:
                fileList = self.item.parent().centralWidget.fileList
            fileList.append(loadPath)
            try:
                self.item.loadedFiles.append(loadPath)
            except AttributeError:
                print("This is the general file browser")
            else:
                print("This is the blockitem file browser")

    def delFile(self):
        """
        Deletes the selected file from the folder
        """
        print("Deleting file")
        filePath = self.rreplace(str(self.getSelectedFile()), "/", "\\", 1)
        if filePath == 0:
            return
        try:
            os.remove(filePath)
            try:
                self.item.parent.parent().fileList.remove(str(filePath))
            except AttributeError:
                print("find this", self.item.parent().centralWidget.fileList[0], filePath)
                self.item.parent().centralWidget.fileList.remove(str(filePath))
        except OSError:
            msg = QMessageBox()
            msg.setText("Cannot delete folder!")
            msg.exec_()

    def rreplace(self, string, old, new, occurrence):
        li = string.rsplit(old, occurrence)
        return new.join(li)

    def editPriority(self):
        priority = self.getInteger()
        index = self.currentIndex()
        self.model.setData(index, priority, Qt.DisplayRole)
        print(self.model.itemData(index))

    def getFilePath(self):
        """
        Get the index of the selected file.
        If nothing is selected, get the index of the top file
        """
        index = self.currentIndex()
        return self.model.filePath(index)

    def getSelectedFile(self):
        """
        Gets the selected file, used for delection.
        """
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            msg = QMessageBox()
            msg.setText("No item at current position!")
            msg.exec_()
            return 0
        else:
            return self.model.filePath(index)

    def getInteger(self):
        i, okPressed = QInputDialog.getInt(self, "Get integer", "Value:", 28, 0, 100, 1)
        if okPressed:
            return i

