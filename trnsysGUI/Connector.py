# pylint: skip-file
# type: ignore

import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class Connector(BlockItem):
    def __init__(self, trnsysType, parent):
        super().__init__(trnsysType, parent)
        self.sizeFactor = 0.5
        self.w = 40
        self.h = 40

        self.inputs.append(PortItem("i", 0, self))
        self.outputs.append(PortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.CONNECTOR_PNG

    def changeSize(self):
        w = self.w
        h = self.h

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

        deltaH = self.h / 8

        self.origInputsPos = [[0, delta]]
        self.origOutputsPos = [[w, delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        # self.inputs[0].side = 0 + 2 * self.flippedH
        # self.outputs[0].side = 2 - 2 * self.flippedH
        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

    def exportBlackBox(self):
        return "noBlackBoxOutput", []
