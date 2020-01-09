from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class TVentil(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(TVentil, self).__init__(trnsysType, parent, kwargs)
        factor = 0.6
        self.w = 100 * factor
        self.h = 61.14 * factor
        self.typeNumber = 3
        self.isComplexDiv = False

        self.inputs.append(PortItem('o', 0, self))
        self.inputs.append(PortItem('o', 1, self))
        self.outputs.append(PortItem('i', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h

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

        deltaH = self.h / 18
        self.inputs[0].setPos(- 2 * delta + 4 * self.flippedH * delta + w * self.flippedH,
                              h / 2 + deltaH - 2 * deltaH * self.flippedV)
        self.inputs[1].setPos(w / 2, -2 * delta + 4 * delta * self.flippedV + h * self.flippedV)
        self.outputs[0].setPos(w + 2 * delta - self.flippedH * w - 4 * self.flippedH * delta,
                               h / 2 + deltaH - 2 * deltaH * self.flippedV)

        self.inputs[0].side = 0 + 2 * self.flippedH
        self.inputs[1].side = 1 + 2 * self.flippedH
        self.outputs[0].side = 2 - 2 * self.flippedH

        return w, h

    def setComplexDiv(self, b):
        self.isComplexDiv = b