import pathlib as _pl
import typing as _tp

import trnsysGUI.BlockItem as _bi
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


class SourceSinkBase(_bi.BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 60
        self.h = 60

        self.inputs.append(_cspi.createSinglePipePortItem("i", 1, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 1, self))

        self.changeSize()

        self._updateDdckFilePath()

    def getDisplayName(self) -> str:
        return self.displayName

    def setDisplayName(self, newName: str) -> None:
        super().setDisplayName(newName)
        self._updateDdckFilePath()

    def _updateDdckFilePath(self):
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

    def getInternalPiping(self) -> _ip.InternalPiping:
        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        pump = _mfn.Pump(inputPort, outputPort)

        modelPortItemsToGraphicalPortItem = {inputPort: self.inputs[0], outputPort: self.outputs[0]}
        return _ip.InternalPiping([pump], modelPortItemsToGraphicalPortItem)

    def exportMassFlows(self):
        equationNr = 1
        massFlowLine = f"Mfr{self.displayName} = 500\n"
        return massFlowLine, equationNr
