import typing as _tp

import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.connectors.doublePipeConnectorBase as _dpcb
import trnsysGUI.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.temperatures as _temps
from trnsysGUI.massFlowSolver import networkModel as _mfn


class SingleDoublePipeConnector(_dpcb.DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_dppi.DoublePipePortItem("o", 2, self))

        self._updateModels(self.displayName)

        self.changeSize()

    def _updateModels(self, newDisplayName: str) -> None:
        coldInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
        coldOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.STANDARD)
        self._coldPipe = _mfn.Pipe(coldInput, coldOutput, name="Cold")

        hotInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.STANDARD)
        hotOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
        self._hotPipe = _mfn.Pipe(hotInput, hotOutput, name="Hot")

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

    def getInternalPiping(self) -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self._coldPipe.fromPort: self.outputs[0],
            self._coldPipe.toPort: self.inputs[1],
        }
        hotModelPortItemsToGraphicalPortItem = {
            self._hotPipe.fromPort: self.inputs[0],
            self._hotPipe.toPort: self.outputs[0],
        }
        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
        internalPiping = _ip.InternalPiping([self._coldPipe, self._hotPipe], modelPortItemsToGraphicalPortItem)
        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:  # pylint: disable=too-many-locals
        doubleConnection = self.outputs[0].getConnection()
        assert isinstance(doubleConnection, _dpc.DoublePipeConnection)

        hotInputSingleConnection = self.inputs[0].getConnection()
        assert isinstance(hotInputSingleConnection, _spc.SinglePipeConnection)

        coldOutputSingleConnection = self.inputs[1].getConnection()
        assert isinstance(coldOutputSingleConnection, _spc.SinglePipeConnection)

        coldUnit = self._getColdPipeIfThenElseUnit(startingUnit, doubleConnection, coldOutputSingleConnection)

        hotUnit = self._getHotPipeIfThenElseUnit(startingUnit + 1, hotInputSingleConnection, doubleConnection)

        unitText = f"""\
{coldUnit}
{hotUnit}
"""
        return unitText, startingUnit + 2

    def _getColdPipeIfThenElseUnit(
        self,
        unitNumber: int,
        doubleConnection: _dpc.DoublePipeConnection,
        coldOutputSingleConnection: _spc.SinglePipeConnection,
    ) -> str:
        coldOutputTemp = _temps.getTemperatureVariableName(self, self._coldPipe)

        coldMfr = _helpers.getInputMfrName(self, self._coldPipe)

        posFlowColdInputTemp = _helpers.getTemperatureVariableName(
            doubleConnection, self.outputs[0], _mfn.PortItemType.COLD
        )

        negFlowColdInputTemp = _helpers.getTemperatureVariableName(
            coldOutputSingleConnection, self.inputs[1], _mfn.PortItemType.STANDARD
        )

        coldEquation = _helpers.getIfThenElseUnit(
            unitNumber, coldOutputTemp, coldMfr, posFlowColdInputTemp, negFlowColdInputTemp
        )

        return coldEquation

    def _getHotPipeIfThenElseUnit(
        self,
        unitNumber: int,
        hotInputSingleConnection: _spc.SinglePipeConnection,
        doubleConnection: _dpc.DoublePipeConnection,
    ) -> str:
        hotOutputTemp = _temps.getTemperatureVariableName(self, self._hotPipe)

        hotMfr = _helpers.getInputMfrName(self, self._hotPipe)

        posFlowHotInputTemp = _helpers.getTemperatureVariableName(
            hotInputSingleConnection, self.inputs[0], _mfn.PortItemType.STANDARD
        )

        negFlowHotInputTemp = _helpers.getTemperatureVariableName(
            doubleConnection, self.outputs[0], _mfn.PortItemType.HOT
        )
        hotEquation = _helpers.getIfThenElseUnit(
            unitNumber, hotOutputTemp, hotMfr, posFlowHotInputTemp, negFlowHotInputTemp
        )

        return hotEquation
