import os
import shutil

from PyQt5.QtWidgets import QTreeView

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PortItem import PortItem


class Radiator(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(Radiator, self).__init__(trnsysType, parent, **kwargs)

        self.inputs.append(PortItem('i', 0, self))
        self.outputs.append(PortItem('o', 0, self))
        self.loadedFiles = []

        self.changeSize()
        self.addTree()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 1
        deltaH = self.h / 20

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40
        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.outputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w,
                               h - h * self.flippedV - deltaH + 2 * deltaH * self.flippedV)
        self.inputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w,
                              h * self.flippedV + deltaH - 2 * deltaH * self.flippedV)
        # self.inputs[0].side = 0 + 2 * self.flippedH
        # self.outputs[0].side = 0 + 2 * self.flippedH
        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        print(self.parent.parent())
        pathName = 'Radiator_' + self.displayName
        if self.parent.parent().projectPath =='':
            # self.path = os.path.dirname(__file__)
            # self.path = os.path.join(self.path, 'default')
            self.path = self.parent.parent().tempPath
            # now = datetime.now()
            # self.fileName = now.strftime("%Y%m%d%H%M%S")
            # self.path = os.path.join(self.path, self.fileName)
        else:
            self.path = self.parent.parent().projectPath
        self.path = os.path.join(self.path, 'ddck')
        self.path = os.path.join(self.path, pathName)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.model = MyQFileSystemModel()
        self.model.setRootPath(self.path)
        self.model.setName(self.displayName)
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.path))
        self.tree.setObjectName("%sTree" % self.displayName)
        for i in range(1, self.model.columnCount()-1):
            self.tree.hideColumn(i)
        self.tree.setMinimumHeight(200)
        self.tree.setSortingEnabled(True)
        self.parent.parent().splitter.addWidget(self.tree)

    # def loadFile(self, file):
    #     filePath = self.parent.parent().projectPath
    #     msgB = QMessageBox()
    #     if filePath == '':
    #         msgB.setText("Please select a project path before loading!")
    #         msgB.exec_()
    #     else:
    #         print("file loaded into %s" % filePath)
    #         shutil.copy(file, filePath)

    def updateTreePath(self, path):
        """
        When the user chooses the project path for the file explorers, this method is called
        to update the root path.
        """
        pathName = 'Radiator_' + self.displayName
        self.path = os.path.join(path, "ddck")
        self.path = os.path.join(self.path, pathName)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.model.setRootPath(self.path)
        self.tree.setRootIndex(self.model.index(self.path))

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
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName+'Tree')
        shutil.rmtree(self.path)
        self.deleteLoadedFile()
        try:
            widgetToRemove.hide()
        except AttributeError:
            print("Widget doesnt exist!")
        else:
            print("Deleted widget")
        del self

    def setName(self, newName):
        """
        Overridden method to also change folder name
        """
        self.displayName = newName
        self.label.setPlainText(newName)
        self.model.setName(self.displayName)
        self.tree.setObjectName("%sTree" % self.displayName)
        print(os.path.dirname(self.path))
        destPath = str(os.path.dirname(self.path))+'\\Radiator_'+self.displayName
        if os.path.exists(self.path):
            os.rename(self.path, destPath)
            self.path = destPath
            print(self.path)

    def deleteLoadedFile(self):
        for items in self.loadedFiles:
            try:
                self.parent.parent().fileList.remove(str(items))
            except AttributeError:
                print("find this", self.item.parent().centralWidget.fileList[0], items)
                self.parent().centralWidget.fileList.remove(str(items))