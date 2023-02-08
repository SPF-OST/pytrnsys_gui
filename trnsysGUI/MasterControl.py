# pylint: skip-file
# type: ignore

import os
import shutil

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QTreeView

from trnsysGUI.BlockItem import BlockItem


class MasterControl(BlockItem):
    def __init__(self, trnsysType, editor, **kwargs):
        super(MasterControl, self).__init__(trnsysType, editor, **kwargs)
        factor = 0.667  # 0.63 for png
        self.w = 100
        self.h = 100
        self.loadedFiles = []

        self.editor.controlExists += 1
        self.createControlDir()

    def createControlDir(self):
        if self.editor.projectPath == "":
            projectPath = self.editor.projectFolder
        else:
            projectPath = self.editor.projectPath

        self.editor.controlDirectory = os.path.join(projectPath, "ddck")
        self.editor.controlDirectory = os.path.join(self.editor.controlDirectory, "Master_Control")
        if not os.path.exists(self.editor.controlDirectory):
            os.makedirs(self.editor.controlDirectory)

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        print("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.editor.trnsysObj.remove(self)
        print("deleting block " + str(self) + self.displayName)
        self.editor.diagramView.scene().removeItem(self)
        widgetToRemove = self.editor.findChild(QTreeView, self.displayName + "Tree")
        self.editor.controlExists -= 1
        if self.editor.controlExists == 0:
            shutil.rmtree(self.editor.controlDirectory)

        # self.deleteLoadedFile()
        try:
            widgetToRemove.hide()
        except AttributeError:
            print("Widget doesnt exist!")
        else:
            print("Deleted widget")
        del self
