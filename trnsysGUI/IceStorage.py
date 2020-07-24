from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class IceStorage(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(IceStorage, self).__init__(trnsysType, parent, **kwargs)
        self.w = 120
        self.h = 120
        self.inputs.append(PortItem('i', 2, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h
        deltaH = self.h / 13

        """ Resize block function """
        delta = 20

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

        # If inputs should be on top side:
        # self.inputs[0].setPos(1 / 3 * w + 1 / 3 * w * self.flippedH, h * self.flippedV)
        # self.outputs[0].setPos(2 / 3 * w - 1 / 3 * w * self.flippedH, h * self.flippedV)
        # self.inputs[0].side = 1 + 2 * self.flippedV
        # self.outputs[0].side = 1 + 2 * self.flippedV

        # If inputs are on the (right per default) side
        self.outputs[0].setPos(w,h-delta)
        self.inputs[0].setPos(w,delta)
        # self.inputs[0].side = 2 - 2 * self.flippedH
        # self.outputs[0].side = 1 - 1 * self.flippedH
        self.inputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        return w, h
