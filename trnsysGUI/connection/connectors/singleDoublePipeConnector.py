import typing as _tp

import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.connection.connectors.doublePipeConnectorBase as _dpcb
import trnsysGUI.connection.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.temperatures as _temps
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.globalNames as _gnames


class SingleDoublePipeConnector(_dpcb.DoublePipeConnectorBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.outputs.append(_dppi.DoublePipePortItem("o", self))

        self._setModels()

        self.changeSize()

    def _setModels(self) -> None:
        coldInput = _mfn.PortItem(
            "In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD
        )
        coldOutput = _mfn.PortItem(
            "Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.STANDARD
        )
        self._coldPipe = _mfn.Pipe(coldInput, coldOutput, name="Cold")

        hotInput = _mfn.PortItem(
            "In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.STANDARD
        )
        hotOutput = _mfn.PortItem(
            "Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT
        )
        self._hotPipe = _mfn.Pipe(hotInput, hotOutput, name="Hot")

    @classmethod
    @_tp.override
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.SINGLE_DOUBLE_PIPE_CONNECTOR_SVG

    def changeSize(self):
        super().changeSize()

        self.origInputsPos = [[0, 0], [0, 20]]
        self.origOutputsPos = [[40, 10]]

        self.inputs[0].setPos(
            self.origInputsPos[0][0], self.origInputsPos[0][1]
        )
        self.inputs[1].setPos(
            self.origInputsPos[1][0], self.origInputsPos[1][1]
        )
        self.outputs[0].setPos(
            self.origOutputsPos[0][0], self.origOutputsPos[0][1]
        )

        # pylint: disable=duplicate-code
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

    def getInternalPiping(self) -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self._coldPipe.fromPort: self.outputs[0],
            self._coldPipe.toPort: self.inputs[1],
        }
        hotModelPortItemsToGraphicalPortItem = {
            self._hotPipe.fromPort: self.inputs[0],
            self._hotPipe.toPort: self.outputs[0],
        }
        modelPortItemsToGraphicalPortItem = (
            coldModelPortItemsToGraphicalPortItem
            | hotModelPortItemsToGraphicalPortItem
        )
        internalPiping = _ip.InternalPiping(
            [self._coldPipe, self._hotPipe], modelPortItemsToGraphicalPortItem
        )
        return internalPiping

    def exportPipeAndTeeTypesForTemp(
        self, startingUnit: int
    ) -> _tp.Tuple[str, int]:  # pylint: disable=too-many-locals
        doubleConnection = self.outputs[0].getConnection()
        assert isinstance(doubleConnection, _dpc.DoublePipeConnection)

        hotInputSingleConnection = self.inputs[0].getConnection()
        assert isinstance(hotInputSingleConnection, _spc.SinglePipeConnection)

        coldOutputSingleConnection = self.inputs[1].getConnection()
        assert isinstance(
            coldOutputSingleConnection, _spc.SinglePipeConnection
        )

        coldUnit = self._getColdPipeIfThenElseUnit(
            startingUnit, doubleConnection, coldOutputSingleConnection
        )

        hotUnit = self._getHotPipeIfThenElseUnit(
            startingUnit + 1, hotInputSingleConnection, doubleConnection
        )

        unitText = f"""\
! BEGIN {self.displayName}
! cold pipe
{coldUnit}

! hot pipe
{hotUnit}
! END {self.displayName}


"""
        return unitText, startingUnit + 2

    def _getColdPipeIfThenElseUnit(
        self,
        unitNumber: int,
        doubleConnection: _dpc.DoublePipeConnection,
        coldOutputSingleConnection: _spc.SinglePipeConnection,
    ) -> str:
        coldOutputTemp = _temps.getTemperatureVariableName(
            self.shallRenameOutputTemperaturesInHydraulicFile(),
            componentDisplayName=self.displayName,
            nodeName=self._coldPipe.name,
        )

        coldMfr = _helpers.getInputMfrName(self.displayName, self._coldPipe)

        posFlowColdInputTemp = _helpers.getTemperatureVariableName(
            doubleConnection, self.outputs[0], _mfn.PortItemType.COLD
        )

        negFlowColdInputTemp = _helpers.getTemperatureVariableName(
            coldOutputSingleConnection,
            self.inputs[1],
            _mfn.PortItemType.STANDARD,
        )

        coldEquation = _helpers.getIfThenElseUnit(
            unitNumber,
            coldOutputTemp,
            _gnames.DoublePipes.INITIAL_COLD_TEMPERATURE,
            coldMfr,
            posFlowColdInputTemp,
            negFlowColdInputTemp,
            extraNewlines="",
        )

        return coldEquation

    def _getHotPipeIfThenElseUnit(
        self,
        unitNumber: int,
        hotInputSingleConnection: _spc.SinglePipeConnection,
        doubleConnection: _dpc.DoublePipeConnection,
    ) -> str:
        hotOutputTemp = _temps.getTemperatureVariableName(
            self.shallRenameOutputTemperaturesInHydraulicFile(),
            componentDisplayName=self.displayName,
            nodeName=self._hotPipe.name,
        )

        hotMfr = _helpers.getInputMfrName(self.displayName, self._hotPipe)

        posFlowHotInputTemp = _helpers.getTemperatureVariableName(
            hotInputSingleConnection,
            self.inputs[0],
            _mfn.PortItemType.STANDARD,
        )

        negFlowHotInputTemp = _helpers.getTemperatureVariableName(
            doubleConnection, self.outputs[0], _mfn.PortItemType.HOT
        )
        hotEquation = _helpers.getIfThenElseUnit(
            unitNumber,
            hotOutputTemp,
            _gnames.SinglePipes.INITIAL_TEMPERATURE,
            hotMfr,
            posFlowHotInputTemp,
            negFlowHotInputTemp,
            extraNewlines="",
        )

        return hotEquation
