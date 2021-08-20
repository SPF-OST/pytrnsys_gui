# pylint: skip-file
# type: ignore

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
        self.logger = blockitem.logger
        self.setContextMenuPolicy(True)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.model = model
        self.item = blockitem

        # for i in range(1, self.model.columnCount()-1):
        #     self.logger.debug('Is column %i hidden : %r' % (i, self.isColumnHidden(i)))
        #     self.hideColumn(i)
        #     self.logger.debug('Is column %i hidden : %r' % (i, self.isColumnHidden(i)))

    def mouseDoubleClickEvent(self, event):
        self.logger.debug("Double clicked")
        self.openFile()

    def mousePressEvent(self, event):
        self.clearSelection()
        QTreeView.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
        menu = QMenu()

        # open = menu.addAction("Open")
        # open.triggered.connect(self.openFile)

        load = menu.addAction("Load")
        load.triggered.connect(self.loadFile)

        # editP = menu.addAction("Load profile")
        # editP.triggered.connect(self.loadProfile)

        dele = menu.addAction("Delete")
        dele.triggered.connect(self.delFile)

        menu.exec_(event.globalPos())

    def openFile(self):
        """
        When double click on a row, this method is called to open the double clicked file
        """
        self.logger.debug("Opening file")
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
        filePath = self.getFilePath()
        fileName = QFileDialog.getOpenFileName(self, "Load file")[0]
        simpFileName = os.path.split(fileName)[-1]
        loadPath = os.path.join(filePath, simpFileName)
        self.logger.debug(loadPath)
        if fileName != "":
            self.logger.info("file loaded into %s" % filePath)
            if Path(loadPath).exists():
                qmb = QMessageBox()
                qmb.setText(
                    "Warning: " + "A file with the same name exists already. Do you want to overwrite or cancel?"
                )
                qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                qmb.setDefaultButton(QMessageBox.Cancel)
                ret = qmb.exec()
                if ret == QMessageBox.Save:
                    self.logger.debug("Overwriting")
                    # continue
                else:
                    self.logger.debug("Canceling")
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
                self.logger.debug("This is the general file browser")
            else:
                self.logger.debug("This is the blockitem file browser")
        else:
            self.logger.info("file loading cancelled")

    def delFile(self):
        """
        Deletes the selected file from the folder
        """
        self.logger.debug("Deleting file")
        filePath = self.rreplace(str(self.getSelectedFile()), "/", "\\", 1)
        if filePath == 0:
            return
        try:
            os.remove(filePath)
            # try:
            #     self.item.parent.parent().fileList.remove(str(filePath))
            # except AttributeError:
            #     try:
            #         self.item.parent().centralWidget.fileList.remove(str(filePath))
            #     except ValueError:
            #         try:
            #             self.item.parent().centralWidget.fileList.remove(str(filePath).replace('/', '\\'))
            #         except:
            #             pass

        except OSError:
            msg = QMessageBox()
            msg.setText("Cannot delete file!")
            msg.exec_()

    def rreplace(self, string, old, new, occurrence):
        li = string.rsplit(old, occurrence)
        return new.join(li)

    # def loadProfile(self):
    #     filePath = self.model.rootPath()
    #     fileName = QFileDialog.getOpenFileName(self, "Load file")[0]
    #     self.logger.debug("filepath: " + filePath)
    #     simpFileName = fileName.split("/ddck/")[-1]
    #     profileName = fileName.split("/")[-1]
    #     self.logger.debug("simpefilename: " + simpFileName)
    #     loadPath = os.path.join(filePath, simpFileName)
    #     self.logger.debug("loadpath: " + loadPath)
    #     if fileName != '':
    #         directory = loadPath.split(profileName)[0]
    #         self.logger.debug("directory: " + directory)
    #         self.logger.info("profile loaded into %s" % filePath)
    #         if Path(loadPath).exists():
    #             qmb = QMessageBox()
    #             qmb.setText("Warning: " +
    #                         "A profile with the same name exists already. Do you want to overwrite or cancel?")
    #             qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
    #             qmb.setDefaultButton(QMessageBox.Cancel)
    #             ret = qmb.exec()
    #             if ret == QMessageBox.Save:
    #                 self.logger.debug("Overwriting")
    #                 shutil.copy(fileName, loadPath)
    #                 # continue
    #             else:
    #                 self.logger.debug("Canceling")
    #                 return
    #         else:
    #             if not os.path.exists(directory):
    #                 os.makedirs(directory)
    #             shutil.copy(fileName, loadPath)
    #     else:
    #         self.logger.info("file loading cancelled")

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
