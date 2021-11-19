import typing as _tp

import massFlowSolver.networkModel as _mfn  # type: ignore[attr-defined]
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.DoublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.SinglePipePortItem import SinglePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.doublePipeConnectorBase import DoublePipeConnectorBase


class SingleDoublePipeConnector(DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SINGLE_DOUBLE_PIPE_CONNECTOR_SVG

    def changeSize(self):
        super().changeSize()

        self.origInputsPos = [[0, 0], [0, 20]]
        self.origOutputsPos = [[20, 10]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        # pylint: disable=duplicate-code  # 2
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 * self.flippedH) % 4
        # pylint: disable=duplicate-code  # 2
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

    def getInternalPiping(self) -> InternalPiping:
        coldInput: _mfn.PortItem = ColdPortItem()
        coldOutput: _mfn.PortItem = ColdPortItem()
        coldConnector = _mfn.Pipe(self.displayName + "Cold", self.childIds[0], coldInput, coldOutput)
        coldModelPortItemsToGraphicalPortItem = {coldInput: self.outputs[0], coldOutput: self.inputs[1]}

        hotInput: _mfn.PortItem = HotPortItem()
        hotOutput: _mfn.PortItem = HotPortItem()
        hotConnector = _mfn.Pipe(self.displayName + "Hot", self.childIds[1], hotInput, hotOutput)
        hotModelPortItemsToGraphicalPortItem = {hotInput: self.inputs[0], hotOutput: self.outputs[0]}

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldConnector, hotConnector], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        unitNumber = startingUnit
        unitText = ""

        unitText += self._getEquation(self.inputs[0], "Cold")
        unitText += self._getEquation(self.inputs[1], "Hot")

        unitNumber += 1

        return unitText, unitNumber

    def _getEquation(self, inp, temperature):
        unitText = "!" + self.displayName + temperature + "\n"
        unitText += "EQUATIONS 1\n"

        tIn = f"GT(Mfr{self.displayName}{temperature}_A, 0)*T{inp.connectionList[0].displayName} + " \
              f"LT(Mfr{self.displayName}{temperature}_A, 0)*" \
              f"T{self.outputs[0].connectionList[0].displayName}{temperature}"  # pylint: disable=duplicate-code
        tOut = f"T{self.displayName}{temperature}"
        unitText += f"{tOut} = {tIn}\n\n"
        return unitText

    def getTemperatureVariableName(self, portItem) -> str:
        internalPiping = self.getInternalPiping()

        startingNodes = internalPiping.openLoopsStartingNodes
        assert all(isinstance(n, _mfn.Pipe) for n in startingNodes)
        internalPipes = [_tp.cast(_mfn.Pipe, n) for n in startingNodes]

        graphicalPortItems = internalPiping.modelPortItemsToGraphicalPortItem

        keyPortItems = [key for key, value in graphicalPortItems.items() if value == portItem]
        assert len(keyPortItems) == 1, "portItem is not unique"
        keyPortItem = keyPortItems[0]

        for internalPipe in internalPipes:
            if keyPortItem in (internalPipe.fromNode, internalPipe.toNode):
                return "T" + internalPipe.name

        raise AssertionError("Found no internal SingleDoublePipeConnector-Connection.")
