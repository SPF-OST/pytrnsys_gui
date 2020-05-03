import os

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QTreeView, QMenu, QMessageBox


class MyQTreeView(QTreeView):
    def __init__(self, model, blockitem):
        super(QTreeView, self).__init__()
        self.setContextMenuPolicy(True)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.model = model
        self.item = blockitem

    def mouseDoubleClickEvent(self, event):
        print("Double clicked")
        self.openFile()

    def contextMenuEvent(self, event):
        menu = QMenu()

        open = menu.addAction("Open")
        open.triggered.connect(self.openFile)

        load = menu.addAction("Load")
        load.triggered.connect(self.loadFile)

        menu.exec_(event.globalPos())

    def openFile(self):
        print("Opening file")
        filePath = self.getFilePath()
        try:
            os.startfile(filePath)
        except OSError:
            msg = QMessageBox()
            msg.setText("No application is associated with the specified file for this operation")
            msg.exec_()

    def loadFile(self):
        filePath = self.getFilePath()
        print("Loading file")
        self.item.loadFile(filePath)

    def getFilePath(self):
        index = self.currentIndex()
        return self.model.filePath(index)
