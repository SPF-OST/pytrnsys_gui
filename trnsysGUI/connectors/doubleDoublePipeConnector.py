from __future__ import annotations

import typing as _tp

import trnsysGUI.connectors.doublePipeConnectorBase as _dpcb
import trnsysGUI.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps


class DoubleDoublePipeConnector(_dpcb.DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(_dppi.DoublePipePortItem("i", 0, self))
        self.outputs.append(_dppi.DoublePipePortItem("o", 2, self))

        self._updateModels(self.displayName)

        self.changeSize()

    def _updateModels(self, newDisplayName: str) -> None:
        coldInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
        coldOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
        self._coldPipe = _mfn.Pipe(coldInput, coldOutput, "Cold")

        hotInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
        hotOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
        self._hotPipe = _mfn.Pipe(hotInput, hotOutput, "Hot")

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

    def getInternalPiping(self) -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self._coldPipe.fromPort: self.outputs[0],
            self._coldPipe.toPort: self.inputs[0],
        }

        hotModelPortItemsToGraphicalPortItem = {
            self._hotPipe.fromPort: self.inputs[0],
            self._hotPipe.toPort: self.outputs[0],
        }

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem

        internalPiping = _ip.InternalPiping(
            [self._coldPipe, self._hotPipe], modelPortItemsToGraphicalPortItem
        )

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        inputPort = self.inputs[0]
        outputPort = self.outputs[0]

        assert isinstance(inputPort, _dppi.DoublePipePortItem)
        assert isinstance(outputPort, _dppi.DoublePipePortItem)

        hotEquation = self._getEquation(self._hotPipe, inputPort, outputPort)
        coldEquation = self._getEquation(self._coldPipe, outputPort, inputPort)

        equations = f"""\
EQUATIONS 2
{coldEquation}
{hotEquation}
"""
        return equations, startingUnit

    def _getEquation(
        self,
        pipe: _mfn.Pipe,
        fromPort: _dppi.DoublePipePortItem,
        toPort: _dppi.DoublePipePortItem
    ) -> str:
        outputTemp = _temps.getTemperatureVariableName(self, self._hotPipe)
        fromConnection = fromPort.getConnection()
        toConnection = toPort.getConnection()

        mfr = _helpers.getInputMfrName(self, pipe)

        posFlowInputConnectionNode = fromConnection.getInternalPiping().getNode(
            fromPort, pipe.fromPort.type
        )
        posFlowInputTemp = _temps.getTemperatureVariableName(fromConnection, posFlowInputConnectionNode)

        negFlowInputConnectionNode = toConnection.getInternalPiping().getNode(
            toPort, pipe.toPort.type
        )
        negFlowInputTemp = _temps.getTemperatureVariableName(toConnection, negFlowInputConnectionNode)

        hotEquation = _helpers.getEquation(outputTemp, mfr, posFlowInputTemp, negFlowInputTemp)
        return hotEquation
