from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QImage, QCursor, QIcon
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QGraphicsPixmapItem, QMenu, QFileDialog

from trnsysGUI.ResizerItem import ResizerItem


class GraphicalItem(QGraphicsPixmapItem):
    def __init__(self, parent, **kwargs):

        super(GraphicalItem, self).__init__(None)
        self.w = 100.0
        self.h = 100.0
        self.parent = parent
        self.resizeMode = False
        self.id = self.parent.parent().idGen.getID()

        # self.trnsysId = self.parent.parent().idGen.getTrnsysID()
        # if "loadedBlock" not in kwargs:
        #     self.parent.parent().trnsysObj.append(self)

        self.flippedH = False
        self.flippedV = False
        self.rotationN = 0
        # Initial icon
        self.imageSource = "images/gear.svg"
        self.image = QPixmap(QIcon(self.imageSource).pixmap(QSize(self.w, self.h)).toImage())
        self.setPixmap(self.image)

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        # self.resizer = ResizerItem(self)

        # if kwargs == {}:
        #     self.parent.parent().graphicalObj.append(self)
        # else:
        #     if "loadedGI" in kwargs:
        #         pass
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

    def setImageSource(self, s):
        self.imageSource = s

    def updateImage(self):
        if self.imageSource[-3:] == "svg":
            self.image = QPixmap(QIcon(self.imageSource).pixmap(QSize(self.w, self.h)).toImage())
            self.setPixmap(self.image)

        elif self.imageSource[-3:] == "png":
            self.image = QImage(self.imageSource)
            self.setPixmap(QPixmap(self.image).scaled(QSize(self.w, self.h)))

    def encode(self):
        dct = {}

        dct[".__BlockDict__"] = True
        dct["BlockName"] = "GraphicalItem"
        dct["BlockPosition"] = (float(self.pos().x()), float(self.pos().y()))
        dct["ID"] = self.id
        dct["Size"] = self.w, self.h
        dct["ImageSource"] = self.imageSource
        dct["FlippedH"] = self.flippedH
        dct["FlippedV"] = self.flippedV
        dct["RotationN"] = self.rotationN

        dictName = "GraphicalItem-"
        return dictName, dct

    def decode(self, i, resConnList, resBlockList):
        self.imageSource = i["ImageSource"]
        self.setPos(float(i["BlockPosition"][0]), float(i["BlockPosition"][1]))
        self.id = i["ID"]
        self.w, self.h = i["Size"]
        self.updateImage()

        # self.updateFlipStateH(i["FlippedH"])
        # self.updateFlipStateV(i["FlippedV"])
        # self.rotateBlockToN(i["RotationN"])
        # self.displayName = i["BlockDisplayName"]
        # self.label.setPlainText(self.displayName)

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
