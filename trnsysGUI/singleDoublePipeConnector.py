import typing as _tp

import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from massFlowSolver.modelPortItems import ColdPortItem, HotPortItem
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

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

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
        coldInput = ColdPortItem()
        coldOutput = ColdPortItem()
        coldConnector = _mfn.Pipe(self.displayName + "Cold", self.childIds[0], coldInput, coldOutput)
        ColdModelPortItemsToGraphicalPortItem = {coldInput: self.inputs[1], coldOutput: self.outputs[0]}

        hotInput = HotPortItem()
        hotOutput = HotPortItem()
        hotConnector = _mfn.Pipe(self.displayName + "Hot", self.childIds[1], hotInput, hotOutput)
        HotModelPortItemsToGraphicalPortItem = {hotInput: self.inputs[0], hotOutput: self.outputs[0]}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldConnector, hotConnector], ModelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        if self.isVisible():
            unitNumber = startingUnit

            unitText = ""

            openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
            assert len(openLoops) == 2
            temps = ["Cold", "Hot"]

            for index, (openLoop, temp) in enumerate(zip(openLoops, temps)):
                # unitText += "UNIT " + str(unitNumber) + "\n"
                unitText += "!" + self.displayName + temp + "\n\n"

                unitText += "EQUATIONS 1\n"

                tIn = f"GT(Mfr{self.displayName}{temp}_A, 0)*T{self.inputs[index].connectionList[0].displayName} + " \
                      f"LT(Mfr{self.displayName}{temp}_A, 0)*T{self.outputs[0].connectionList[0].displayName}{temp}"
                tOut = f"T{self.displayName}{temp}"
                unitText += f"{tOut} = {tIn}\n\n"

                unitNumber += 1

            return unitText, unitNumber
        else:
            return "", startingUnit

    def getTemperatureVariableName(self, portItem) -> str:
        internalPiping = self.getInternalPiping()
        startingNodes = internalPiping.openLoopsStartingNodes
        graphicalPortItems = internalPiping.modelPortItemsToGraphicalPortItem

        keyPortItems = [key for key, value in graphicalPortItems.items() if value == portItem]
        assert len(keyPortItems) == 1, "portItem is not unique"
        keyPortItem = keyPortItems[0]
        for index in range(len(startingNodes)):
            if startingNodes[index].fromNode == keyPortItem or startingNodes[index].toNode == keyPortItem:
                return "T" + startingNodes[index].name
        raise AssertionError("Found no internal SingleDoublePipeConnector-Connection.")

