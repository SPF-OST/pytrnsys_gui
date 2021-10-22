# pylint: skip-file
# type: ignore

import typing as _tp

import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from trnsysGUI.BlockItem import BlockItem
from massFlowSolver import InternalPiping
from trnsysGUI.SinglePipePortItem import SinglePipePortItem


class WTap_main(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(WTap_main, self).__init__(trnsysType, parent, **kwargs)
        self.w = 40
        self.h = 40

        self.outputs.append(SinglePipePortItem("o", 0, self))

        self.typeNumber = 4

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.W_TAP_MAIN_SVG

    def changeSize(self):
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

        self.origOutputsPos = [[0, delta]]
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4

        return w, h

    def exportBlackBox(self):
        equation = ["T" + self.displayName + "=Tcw"]
        return "success", equation

    def exportMassFlows(self):
        resStr = "Mfr" + self.displayName + " = 1000" + "\n"
        equationNr = 1
        return resStr, equationNr

    def getInternalPiping(self) -> InternalPiping:
        inputPort = _mfn.PortItem()
        sink = _mfn.Source(self.displayName, self.trnsysId, inputPort)
        return InternalPiping([sink], {inputPort: self.outputs[0]})
