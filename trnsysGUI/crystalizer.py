import typing as _tp

import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.singlePipePortItem import SinglePipePortItem  # type: ignore[attr-defined]
import massFlowSolver.networkModel as _mfn


class Crystalizer(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 120
        self.h = 40

        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.outputs.append(SinglePipePortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.CRYSTALIZER_SVG

    def changeSize(self):
        width, _ = self._getCappedWithAndHeight()
        self._positionLabel()

        self.origInputsPos = [[0, 20]]
        self.origOutputsPos = [[120, 20]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        # pylint: disable=duplicate-code  # 2
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 + 2 * self.flippedH) % 4

    def exportBlackBox(self):
        status = "noDdckEntry"
        equation = ["T" + self.displayName + "=1"]

        return status, equation

    def getInternalPiping(self) -> InternalPiping:
        inputPort = _mfn.PortItem()
        outputPort = _mfn.PortItem()

        crystalizer = _mfn.Pipe(self.displayName, self.trnsysId, inputPort, outputPort)
        modelPortItemsToGraphicalPortItem = {inputPort: self.inputs[0], outputPort: self.outputs[0]}
        return InternalPiping([crystalizer], modelPortItemsToGraphicalPortItem)
