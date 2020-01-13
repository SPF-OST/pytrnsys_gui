from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class Pump(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(Pump, self).__init__(trnsysType, parent, **kwargs)
        # factor = 0.6 for old pump
        # self.w = 100 * factor
        # self.h = 82 * factor
        self.w = 30
        self.h = 30
        self.typeNumber = 1

        self.inputs.append(PortItem('i', 0, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 4

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
        self.inputs[0].setPos(self.flippedH * w - 2* delta + 2 * delta * self.flippedH, h / 2)
        self.outputs[0].setPos(w - self.flippedH * w - 2* delta * self.flippedH, h / 2)
        self.inputs[0].side = 2 * self.flippedH
        self.outputs[0].side = 2 - 2 * self.flippedH

        return w, h

