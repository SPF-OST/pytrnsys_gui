import os
import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QTreeView

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PortItem import PortItem
from trnsysGUI.ResizerItem import ResizerItem


class AirSourceHP(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(AirSourceHP, self).__init__(trnsysType, parent, **kwargs)
        factor = 0.8
        self.w = 100 * factor
        self.h = 80 * factor
        self.inputs.append(PortItem('i', 2, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h), Qt.IgnoreAspectRatio))

        self.changeSize()
        self.addTree()

    def changeSize(self):
        # print("passing through c change size")
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 2
        deltaH = self.h / 10

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

        # Update port positions:
        self.outputs[0].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w,
                               h - h * self.flippedV - deltaH + 2 * deltaH * self.flippedV)
        self.inputs[0].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w,
                              h * self.flippedV + deltaH - 2 * deltaH * self.flippedV - self.flippedVInt * 5)
        # self.inputs[0].side = 2 - 2 * self.flippedH
        # self.outputs[0].side = 2 - 2 * self.flippedH
        self.inputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

    def addTree(self):
        print(self.parent.parent())
        self.path = os.path.dirname(__file__)
        self.model = MyQFileSystemModel()
        self.model.setRootPath(os.path.dirname(__file__))
        self.model.setName(self.displayName)
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.path))
        self.tree.setObjectName("%sTree" % self.displayName)
        self.tree.setMinimumHeight(200)
        self.tree.setSortingEnabled(True)
        print(self.tree.objectName())
        self.parent.parent().splitter.addWidget(self.tree)

    def loadFile(self, filePath):
        self.filePath = filePath
