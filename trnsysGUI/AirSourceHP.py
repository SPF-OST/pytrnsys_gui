import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap, QImage

from trnsysGUI.BlockItem import BlockItem
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

    def changeSize(self):
        # print("passing through c change size")
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 4
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

    # For resizing, need set imageSource
    # def mousePressEvent(self, event):  # create resizer
    #     try:
    #         self.resizer
    #     except AttributeError:
    #         self.resizer = ResizerItem(self)
    #         self.resizer.setPos(self.w, self.h)
    #         self.resizer.itemChange(self.resizer.ItemPositionChange, self.resizer.pos())
    #     else:
    #         return
    #
    # def setItemSize(self, w, h):
    #     self.w, self.h = w, h
    #
    # def updateImage(self):
    #     if self.imageSource[-3:] == "svg":
    #         self.image = QImage(self.imageSource)
    #         self.setPixmap(QPixmap(self.image).scaled(self.w, self.h, Qt.KeepAspectRatio))
    #         self.updateFlipStateH(self.flippedH)
    #         self.updateFlipStateV(self.flippedV)

        # elif self.imageSource[-3:] == "png":
        #     self.image = QImage(self.imageSource)
        #     self.setPixmap(QPixmap(self.image).scaled(QSize(self.w, self.h)))
        #     self.updateFlipStateH(self.flippedH)
        #     self.updateFlipStateV(self.flippedV)
