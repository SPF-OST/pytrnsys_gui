# pylint: skip-file
# type: ignore

import os
import shutil

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QTreeView

from trnsysGUI.BlockItem import BlockItem


class MasterControl(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(MasterControl, self).__init__(trnsysType, parent, **kwargs)
        factor = 0.667  # 0.63 for png
        self.w = 100
        self.h = 100
        self.loadedFiles = []

        self.parent.parent().controlExists += 1
        self.createControlDir()

    def createControlDir(self):
        if self.parent.parent().projectPath == "":
            projectPath = self.parent.parent().projectFolder
        else:
            projectPath = self.parent.parent().projectPath

        self.parent.parent().controlDirectory = os.path.join(projectPath, "ddck")
        self.parent.parent().controlDirectory = os.path.join(self.parent.parent().controlDirectory, "Master_Control")
        if not os.path.exists(self.parent.parent().controlDirectory):
            os.makedirs(self.parent.parent().controlDirectory)

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        print("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        # print("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        print("deleting block " + str(self) + self.displayName)
        # print("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName + "Tree")
        self.parent.parent().controlExists -= 1
        if self.parent.parent().controlExists == 0:
            shutil.rmtree(self.parent.parent().controlDirectory)

        # self.deleteLoadedFile()
        try:
            widgetToRemove.hide()
        except AttributeError:
            print("Widget doesnt exist!")
        else:
            print("Deleted widget")
        del self
