from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class HeatPump(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(HeatPump, self).__init__(trnsysType, parent, kwargs)

        self.inputs.append(PortItem('i', 0, self))
        self.inputs.append(PortItem('i', 2, self))
        self.outputs.append(PortItem('o', 0, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        # For restoring correct order of trnsysObj list
        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

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

        self.inputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, 4 * h / 15)
        self.inputs[1].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w, 4 * h / 15)
        self.inputs[0].side = 0 + 2 * self.flippedH
        self.inputs[1].side = 2 - 2 * self.flippedH

        self.outputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, 2 * h / 3)
        self.outputs[1].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w, 2 * h / 3)
        self.outputs[0].side = 0 + 2 * self.flippedH
        self.outputs[1].side = 2 - 2 * self.flippedH

        return w, h

