from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class Collector(BlockItem):
    def __init__(self, trnsysType, name='Untitled', parent=None):
        super(Collector, self).__init__(trnsysType, name, parent)

        self.inputs.append(PortItem('i', 0, self))
        self.outputs.append(PortItem('o', 2, self))
        print("appended i and o " + str(len(self.outputs)))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

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
                              h * self.flippedV + deltaH - 2 * deltaH * self.flippedV)
        self.inputs[0].side = 2 - 2 * self.flippedH
        self.outputs[0].side = 2 - 2 * self.flippedH

        return w, h

