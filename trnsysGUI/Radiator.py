from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class Radiator(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(Radiator, self).__init__(trnsysType, parent, **kwargs)

        self.inputs.append(PortItem('i', 0, self))
        self.outputs.append(PortItem('o', 0, self))

        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 4
        deltaH = self.h / 20

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

        self.outputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w,
                               h - h * self.flippedV - deltaH + 2 * deltaH * self.flippedV)
        self.inputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w,
                              h * self.flippedV + deltaH - 2 * deltaH * self.flippedV)
        self.inputs[0].side = 0 + 2 * self.flippedH
        self.outputs[0].side = 0 + 2 * self.flippedH

