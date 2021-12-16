import typing as _tp

import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.doublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.doublePipeConnectorBase import DoublePipeConnectorBase
from trnsysGUI.modelPortItems import ColdPortItem, HotPortItem


class DoubleDoublePipeConnector(DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(DoublePipePortItem("i", 0, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.DOUBLE_DOUBLE_PIPE_CONNECTOR_SVG

    def changeSize(self):
        super().changeSize()

        self.origInputsPos = [[0, 10]]
        self.origOutputsPos = [[40, 10]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        # pylint: disable=duplicate-code  # 3
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

    def getInternalPiping(self) -> InternalPiping:
        coldInput: _mfn.PortItem = ColdPortItem()
        coldOutput: _mfn.PortItem = ColdPortItem()
        coldTeePiece = _mfn.Pipe(self.displayName + "Cold", self.childIds[0], coldInput, coldOutput)
        coldModelPortItemsToGraphicalPortItem = {coldInput: self.outputs[0], coldOutput: self.inputs[0]}

        hotInput: _mfn.PortItem = HotPortItem()
        hotOutput: _mfn.PortItem = HotPortItem()
        hotTeePiece = _mfn.Pipe(self.displayName + "Hot", self.childIds[1], hotInput, hotOutput)
        hotModelPortItemsToGraphicalPortItem = {hotInput: self.inputs[0], hotOutput: self.outputs[0]}

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldTeePiece, hotTeePiece], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        unitNumber = startingUnit
        unitText = ""  # pylint: disable=duplicate-code

        unitText += self._getEquation("Cold")
        unitText += self._getEquation("Hot")

        return unitText, unitNumber

    def _getEquation(self, temperature):
        unitText = "!" + self.displayName + temperature + "\n"
        unitText += "EQUATIONS 1\n"

        tIn = f"GT(Mfr{self.displayName}{temperature}_A, 0)*" \
              f"T{self.inputs[0].connectionList[0].displayName}{temperature} + " \
              f"LT(Mfr{self.displayName}{temperature}_A, 0)*" \
              f"T{self.outputs[0].connectionList[0].displayName}{temperature}"
        tOut = f"T{self.displayName}{temperature}"  # pylint: disable=duplicate-code
        unitText += f"{tOut} = {tIn}\n\n"
        return unitText
