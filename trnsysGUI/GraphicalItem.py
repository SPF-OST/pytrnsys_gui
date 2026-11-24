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
    def __init__(self, editor, imageAccessor=None, size=(100, 100), **_):

        super().__init__(None)
        self.w, self.h = size
        self._editor = editor
        self.inputs = []  # symbols have no ports (read while pipes are decoded)
        self.outputs = []
        self.resizeMode = False
        self.id = self._editor.idGen.getID()

        self.flippedH = False
        self.flippedV = False
        self.rotationN = 0
        # Initial icon (a gear unless a symbol from the library is given)
        self._imageAccessor = imageAccessor or _img.GEAR_SVG
        self._setPixmapForSize()

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self._editor.graphicalObj.append(self)

    def _setPixmapForSize(self):
        # An SVG whose viewBox starts at (-m, -m) has a margin m around the drawing: e.g. the electrical
        # terminals of the symbols are drawn on the edge of the drawing and reach into the margin. The margin
        # is drawn outside the item's position and size, so that the edge lies on the grid like the ports.
        marginX = marginY = 0.0
        if isinstance(self._imageAccessor, _ia.SvgImageAccessor):
            viewBox = self._imageAccessor.renderer.viewBoxF()
            margin = -viewBox.x()
            if margin > 0 and viewBox.y() == viewBox.x():
                marginX = margin * self.w / (viewBox.width() - 2 * margin)
                marginY = margin * self.h / (viewBox.height() - 2 * margin)

        pixmap = self._imageAccessor.pixmap(
            width=round(self.w + 2 * marginX), height=round(self.h + 2 * marginY)
        )
        self.setPixmap(pixmap)
        self.setOffset(-marginX, -marginY)

    def itemChange(self, change, value):
        # snap to the grid like the block items, so that the terminals of the symbols lie on grid points
        if change == self.ItemPositionChange and self._editor.snapGrid:
            snapSize = self._editor.snapSize
            return QtCore.QPointF(
                value.x() - value.x() % snapSize,
                value.y() - value.y() % snapSize,
            )
        return super().itemChange(change, value)

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

    def deleteBlock(self):
        if self in self._editor.graphicalObj:
            self._editor.graphicalObj.remove(self)
        if self in self._editor.trnsysObj:
            self._editor.trnsysObj.remove(self)
        if self.scene() is not None:
            self.scene().removeItem(self)

    def setImageSource(self, s: str):
        self._imageAccessor = _ia.createForFile(_pl.Path(s))

    def updateImage(self):
        self._setPixmapForSize()

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
