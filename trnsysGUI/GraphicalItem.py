# pylint: skip-file
# type: ignore

import pathlib as _pl

from PyQt5 import QtCore
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtWidgets import QMenu

import trnsysGUI.imageAccessor as _ia
import trnsysGUI.images as _img


class GraphicalItem(QGraphicsPixmapItem):
    def __init__(self, editor, **_):

        super().__init__(None)
        self.w = 100
        self.h = 100
        self._editor = editor
        self.resizeMode = False
        self.id = self._editor.idGen.getID()

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

        self._editor.graphicalObj.append(self)

    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction("Load different image")
        a1.triggered.connect(self.loadAction)

        a2 = menu.addAction("Delete this block")
        a2.triggered.connect(self.deleteBlock)

        menu.exec_(event.screenPos())

    def loadAction(self):
        fileName = QFileDialog.getOpenFileName(
            self._editor, "Load image", filter="*.png *.svg"
        )[0]
        if fileName[-3:] == "png" or fileName[-3:] == "svg":
            self.setImageSource(fileName)
            self.updateImage()
        else:
            print("No image picked, name is " + fileName)

    def setImageSource(self, s: str):
        self._imageAccessor = _ia.createForFile(_pl.Path(s))

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
        self._imageAccessor = _ia.createFromResourcePath(i["ImageSource"])

        self.setPos(float(i["BlockPosition"][0]), float(i["BlockPosition"][1]))
        self.id = i["ID"]
        self.w, self.h = i["Size"]
        self.updateImage()

        resBlockList.append(self)

    def setParent(self, parent):
        self._editor = parent
        if self not in self._editor.graphicalObj:
            self._editor.graphicalObj.append(self)
