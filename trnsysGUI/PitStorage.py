# pylint: skip-file

import typing as _tp

import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItemFourPorts import BlockItemFourPorts


class PitStorage(BlockItemFourPorts):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)
        self.w = 240
        self.h = 160

        self.changeSize()

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.PIT_STORAGE_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 20

        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.origInputsPos = [[5 * delta, 0], [w - 3 * delta, 0]]
        self.origOutputsPos = [[3 * delta, 0], [w - 5 * delta, 0]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

    def getInternalPiping(self) -> _ip.InternalPiping:
        side1Input = _mfn.PortItem("VarIn", _mfn.PortItemDirection.INPUT)
        side1Output = _mfn.PortItem("DeepOut", _mfn.PortItemDirection.OUTPUT)
        side1Pipe = _mfn.Pipe(side1Input, side1Output, "Side1")

        side2Input = _mfn.PortItem("DeepIn", _mfn.PortItemDirection.INPUT)
        side2Output = _mfn.PortItem("ShlwOut", _mfn.PortItemDirection.OUTPUT)
        side2Pipe = _mfn.Pipe(side2Input, side2Output, "Side2")

        modelPortItemsToGraphicalPortItem = {
            side1Input: self.inputs[0],
            side1Output: self.outputs[0],
            side2Input: self.inputs[1],
            side2Output: self.outputs[1],
        }

        return _ip.InternalPiping([side1Pipe, side2Pipe], modelPortItemsToGraphicalPortItem)
