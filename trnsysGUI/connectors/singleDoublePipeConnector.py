import typing as _tp

import trnsysGUI.connectors.doublePipeConnectorBase as _dpcb
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn

from trnsysGUI import connectorsAndPipesExportHelpers as _helpers


class SingleDoublePipeConnector(_dpcb.DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_dppi.DoublePipePortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SINGLE_DOUBLE_PIPE_CONNECTOR_SVG

    def changeSize(self):
        super().changeSize()

        self.origInputsPos = [[0, 0], [0, 20]]
        self.origOutputsPos = [[40, 10]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        # pylint: disable=duplicate-code
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 * self.flippedH) % 4
        # pylint: disable=duplicate-code
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

    def getInternalPiping(self) -> _mfs.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self._coldPipe.fromPort: self.outputs[0],
            self._coldPipe.toPort: self.inputs[1],
        }
        hotModelPortItemsToGraphicalPortItem = {
            self._hotPipe.fromPort: self.inputs[0],
            self._hotPipe.toPort: self.outputs[0],
        }
        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
        internalPiping = _mfs.InternalPiping([self._coldPipe, self._hotPipe], modelPortItemsToGraphicalPortItem)
        return internalPiping

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

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:  # pylint: disable=too-many-locals
        doubleConnection = self.outputs[0].getConnection()

        hotInputSingleConnection = self.inputs[0].getConnection()
        coldOutputSingleConnection = self.inputs[1].getConnection()

        coldOutputTemp = f"T{self.displayName}Cold"
        coldMfr = _helpers.getMfrName(self._coldPipe)
        posFlowColdInputTemp = f"T{doubleConnection.displayName}Cold"
        negFlowColdInputTemp = f"T{coldOutputSingleConnection.displayName}"

        coldEquation = _helpers.getEquation(
            coldOutputTemp, coldMfr, posFlowColdInputTemp, negFlowColdInputTemp
        )

        hotOutputTemp = f"T{self.displayName}Hot"
        hotMfr = _helpers.getMfrName(self._hotPipe)
        posFlowHotInputTemp = f"T{hotInputSingleConnection.displayName}"
        negFlowHotInputTemp = f"T{doubleConnection.displayName}Hot"

        hotEquation = _helpers.getEquation(
            hotOutputTemp, hotMfr, posFlowHotInputTemp, negFlowHotInputTemp
        )

        equations = f"""\
EQUATIONS 2
{coldEquation}
{hotEquation}
"""
        return equations, startingUnit
