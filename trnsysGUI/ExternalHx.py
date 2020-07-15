from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QTransform

from trnsysGUI.BlockItemFourPorts import BlockItemFourPorts

class ExternalHx(BlockItemFourPorts):
    def __init__(self, trnsysType, parent, **kwargs):
        super(ExternalHx, self).__init__(trnsysType, parent, **kwargs)

        my_transform = QTransform()
        my_transform.rotate(90)
        self.image = self.image.transformed(my_transform)

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 3

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

        self.inputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, h / 5)
        self.inputs[1].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w, h / 5)
        # self.inputs[0].side = 0 + 2 * self.flippedH
        # self.inputs[1].side = 2 - 2 * self.flippedH
        self.inputs[0].side = (self.rotationN +2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        self.outputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, 0.83 * h)
        self.outputs[1].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w, 0.83 * h)
        # self.outputs[0].side = 0 + 2 * self.flippedH
        # self.outputs[1].side = 2 - 2 * self.flippedH
        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h