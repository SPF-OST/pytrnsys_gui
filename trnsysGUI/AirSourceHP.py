import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap, QImage

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem
from trnsysGUI.ResizerItem import ResizerItem


class AirSourceHP(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(AirSourceHP, self).__init__(trnsysType, parent, **kwargs)

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
        delta = 20
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
        self.outputs[0].setPos(w,h-delta)
        self.inputs[0].setPos(w,delta)
        # self.inputs[0].side = 2 - 2 * self.flippedH
        # self.outputs[0].side = 2 - 2 * self.flippedH
        self.inputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

