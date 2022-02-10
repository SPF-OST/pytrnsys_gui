import typing as _tp

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.massFlowSolver import InternalPiping, MassFlowNetworkContributorMixin


class Crystalizer(BlockItem, MassFlowNetworkContributorMixin):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 120
        self.h = 40

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.CRYSTALIZER_SVG

    def changeSize(self):
        self._positionLabel()

        self.origInputsPos = [[0, 20]]
        self.origOutputsPos = [[120, 20]]

        # pylint: disable=duplicate-code  # 2
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 0 + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 + 2 * self.flippedH) % 4
        # pylint: disable=duplicate-code  # 2


    def exportBlackBox(self):
        status = "noDdckEntry"
        equation = ["T" + self.displayName + "=1"]

        return status, equation

    def getInternalPiping(self) -> InternalPiping:
        inputPort = _mfn.PortItem("input", _mfn.PortItemType.INPUT)
        outputPort = _mfn.PortItem("output", _mfn.PortItemType.OUTPUT)

        crystalizer = _mfn.Pipe(self.displayName, self.trnsysId, inputPort, outputPort)
        modelPortItemsToGraphicalPortItem = {inputPort: self.inputs[0], outputPort: self.outputs[0]}
        return InternalPiping([crystalizer], modelPortItemsToGraphicalPortItem)
