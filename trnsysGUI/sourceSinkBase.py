import typing as _tp
import pathlib as _pl

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.massFlowSolver import InternalPiping, MassFlowNetworkContributorMixin


class SourceSinkBase(BlockItem, MassFlowNetworkContributorMixin):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 60
        self.h = 60

        self.inputs.append(_cspi.createSinglePipePortItem("i", 1, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 1, self))

        self.changeSize()

        ddckFilePath = _pl.Path(self.parent.parent().projectPath) / "ddck" / f"{self.displayName}.ddck"

        self.path = str(ddckFilePath)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        raise NotImplementedError()

    def changeSize(self):
        self._positionLabel()

        self.origInputsPos = [[20, 0]]
        self.origOutputsPos = [[40, 0]]

        # pylint: disable=duplicate-code  # 1
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 1 + 2 * self.flippedV) % 4
        self.outputs[0].side = (self.rotationN + 1 + 2 * self.flippedV) % 4
        # pylint: disable=duplicate-code  # 1

    def exportBlackBox(self):
        status = "noDdckEntry"
        equation = ["T" + self.displayName + "=1"]

        return status, equation

    def getInternalPiping(self) -> InternalPiping:
        inputPort = _mfn.PortItem("input", _mfn.PortItemType.INPUT)
        outputPort = _mfn.PortItem("output", _mfn.PortItemType.OUTPUT)

        pump = _mfn.Pump(self.displayName, self.trnsysId, inputPort, outputPort)

        modelPortItemsToGraphicalPortItem = {inputPort: self.inputs[0], outputPort: self.outputs[0]}
        return InternalPiping([pump], modelPortItemsToGraphicalPortItem)

    def exportMassFlows(self):
        equationNr = 1
        massFlowLine = f"Mfr{self.displayName} = 500\n"
        return massFlowLine, equationNr

    def hasDdckPlaceHolders(self):
        return True
