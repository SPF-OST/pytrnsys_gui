from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class WTap_main(BlockItem):
    def __init__(self, trnsysType, name='Untitled', parent=None):
        super(WTap_main, self).__init__(trnsysType, name, parent)
        factor = 0.5
        self.w = 100 * factor
        self.h = 100 * factor
        self.inputs.append(PortItem('i', 0, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 4
        deltaHF = 0.45

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

        self.inputs[0].setPos(-2 * delta + (4 * delta + w) * self.flippedH, h / 2)
        print(self.inputs[0].pos())
        print(self.inputs[0].scenePos())
        self.inputs[0].side = 0 + 2 * self.flippedH

        return w, h
