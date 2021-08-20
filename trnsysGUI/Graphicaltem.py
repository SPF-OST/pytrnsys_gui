# pylint: skip-file
# type: ignore

import pathlib as _pl

from PyQt5 import QtCore
from PyQt5.QtGui import QCursor, QPixmap
from PyQt5.QtWidgets import QGraphicsPixmapItem, QMenu, QFileDialog

import trnsysGUI.imageAccessor as _ia
import trnsysGUI.images as _img
from trnsysGUI.ResizerItem import ResizerItem


class GraphicalItem(QGraphicsPixmapItem):
    def __init__(self, parent, **_):

        super(GraphicalItem, self).__init__(None)
        self.w = 100
        self.h = 100
        self.parent = parent
        self.resizeMode = False
        self.id = self.parent.parent().idGen.getID()

        self.flippedH = False
        self.flippedV = False
        self.rotationN = 0
        # Initial icon
        self._imageAccessor = _img.GEAR_SVG
        pixmap = _img.GEAR_SVG.pixmap(width=self.w, height=self.h)
        self.setPixmap(pixmap)

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.parent.parent().graphicalObj.append(self)

    def setItemSize(self, w, h):
        self.w, self.h = w, h

    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction("Load different image")
        a1.triggered.connect(self.loadAction)

        a2 = menu.addAction("Delete this block")
        a2.triggered.connect(self.deleteBlock)

        menu.exec_(event.screenPos())

    def loadAction(self):
        fileName = QFileDialog.getOpenFileName(self.parent.parent(), "Load image", filter="*.png *.svg")[0]
        if fileName[-3:] == "png" or fileName[-3:] == "svg":
            self.setImageSource(fileName)
            self.updateImage()
        else:
            print("No image picked, name is " + fileName)

    def setImageSource(self, s: str):
        self._imageAccessor = _ia.ImageAccessor.createForFile(_pl.Path(s))

    def updateImage(self):
        pixmap = self._imageAccessor.pixmap(width=self.w, height=self.h)
        self.setPixmap(pixmap)

    def encode(self):
        dct = {}

        dct[".__BlockDict__"] = True
        dct["BlockName"] = "GraphicalItem"
        dct["BlockPosition"] = (float(self.pos().x()), float(self.pos().y()))
        dct["ID"] = self.id
        dct["Size"] = self.w, self.h
        dct["ImageSource"] = self._imageAccessor.getResourcePath()
        dct["FlippedH"] = self.flippedH
        dct["FlippedV"] = self.flippedV
        dct["RotationN"] = self.rotationN

        dictName = "GraphicalItem-"
        return dictName, dct

    def decode(self, i, resBlockList):
        self._imageAccessor = _ia.ImageAccessor.createFromResourcePath(i["ImageSource"])

        self.setPos(float(i["BlockPosition"][0]), float(i["BlockPosition"][1]))
        self.id = i["ID"]
        self.w, self.h = i["Size"]
        self.updateImage()

        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self.setPos(float(i["BlockPosition"][0] + offset_x), float(i["BlockPosition"][1] + offset_y))

        # self.updateFlipStateH(i["FlippedH"])
        # self.updateFlipStateV(i["FlippedV"])
        # self.rotateBlockToN(i["RotationN"])

        resBlockList.append(self)

    def setParent(self, parent):
        self.parent = parent
        if self not in self.parent.parent().graphicalObj:
            self.parent.parent().graphicalObj.append(self)

    def deleteBlock(self):
        # self.parent.parent().trnsysObj.remove(self)
        self.parent.parent().graphicalObj.remove(self)
        self.parent.scene().removeItem(self)
        del self

    def mousePressEvent(self, event):
        try:
            self.resizer
        except AttributeError:
            self.resizer = ResizerItem(self)
            self.resizer.setPos(self.w, self.h)
            self.resizer.itemChange(self.resizer.ItemPositionChange, self.resizer.pos())
        else:
            return
        # self.resizer = ResizerItem(self)
        # self.resizer.setPos(self.w, self.h)
        # self.resizer.itemChange(self.resizer.ItemPositionChange, self.resizer.pos())

    def deleteResizer(self):
        del self.resizer
