from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class GroundSourceHx(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        print("sdf")
        super(GroundSourceHx, self).__init__(trnsysType, parent, **kwargs)
        print("c gs")
        self.w = 60
        self.h = 80
        self.inputs.append(PortItem('i', 0, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.changeSize()

    def changeSize(self):
        print("passing through c change size")
        w = self.w
        h = self.h

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

        # Update port positions:
        self.outputs[0].setPos(delta,0)
        self.inputs[0].setPos(w-delta,0)

        self.inputs[0].side = (self.rotationN + 1 + 2 * self.flippedV) % 4
        self.outputs[0].side = (self.rotationN + 1 + 2 * self.flippedV) % 4

        return w, h