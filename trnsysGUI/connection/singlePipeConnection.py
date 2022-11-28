from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.TVentil as _tventil
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.deleteSinglePipeConnectionCommand as _dspc
import trnsysGUI.connection.singlePipeConnectionModel as _model
import trnsysGUI.connection.values as _values
import trnsysGUI.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.hydraulicLoops.names as _names
import trnsysGUI.internalPiping as _pi
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.singlePipePortItem as _sppi
import trnsysGUI.singlePipeSegmentItem as _spsi
import trnsysGUI.temperatures as _temps
from . import _massFlowLabels as _mfl

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class SinglePipeConnection(_cb.ConnectionBase):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        fromPort: _sppi.SinglePipePortItem,
        toPort: _sppi.SinglePipePortItem,
        parent: _ed.Editor,  # type: ignore[name-defined]
    ):
        super().__init__(fromPort, toPort, parent)

        self._editor = parent

        self.diameterInCm: _values.Value = _values.DEFAULT_DIAMETER_IN_CM
        self.uValueInWPerM2K: _values.Value = _values.DEFAULT_U_VALUE_IN_W_PER_M2_K
        self.lengthInM: _values.Value = _values.DEFAULT_LENGTH_IN_M

        self.shallCreateTrnsysUnit = True

        self._updateModels(self.displayName)

    @property
    def fromPort(self) -> _sppi.SinglePipePortItem:
        assert isinstance(self._fromPort, _sppi.SinglePipePortItem)
        return self._fromPort

    @property
    def toPort(self) -> _sppi.SinglePipePortItem:
        assert isinstance(self._toPort, _sppi.SinglePipePortItem)
        return self._toPort

    def getModelPipe(self, portItemType: _mfn.PortItemType) -> _mfn.Pipe:
        if portItemType != _mfn.PortItemType.STANDARD:
            raise ValueError(
                f"Single pipe connections can only have model port items of type {_mfn.PortItemType.STANDARD}"
            )

        return self.modelPipe

    def _createSegmentItem(self, startNode, endNode):
        return _spsi.SinglePipeSegmentItem(startNode, endNode, self)

    def _updateModels(self, newDisplayName: str) -> None:
        fromPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        toPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        self.modelPipe = _mfn.Pipe(fromPort, toPort)

    def getRadius(self):
        rad = 2
        return rad

    def editHydraulicLoop(self) -> None:
        self._editor.editHydraulicLoop(self)

    def createDeleteUndoCommand(self, parentCommand: _tp.Optional[_qtw.QUndoCommand] = None) -> _qtw.QUndoCommand:
        undoCommand = _dspc.DeleteSinglePipeConnectionCommand(
            self, self._editor.hydraulicLoops, self._editor.fluids.fluids, self._editor.fluids.WATER, parentCommand
        )

        return undoCommand

    def encode(self):
        if len(self.segments) > 0:
            labelPos = self.segments[0].label.pos().x(), self.segments[0].label.pos().y()
            labelMassPos = self.segments[0].labelMass.pos().x(), self.segments[0].labelMass.pos().y()
        else:
            self.logger.debug("This connection has no segment")
            defaultPos = self.fromPort.pos().x(), self.fromPort.pos().y()  # pylint: disable = duplicate-code # 2
            labelPos = defaultPos
            labelMassPos = defaultPos

        corners = []
        for s in self.getCorners():  # pylint: disable=invalid-name
            cornerTupel = (s.pos().x(), s.pos().y())
            corners.append(cornerTupel)

        connectionModel = _model.ConnectionModel(
            self.connId,
            self.displayName,
            self.id,
            corners,
            labelPos,
            labelMassPos,
            self.fromPort.id,
            self.toPort.id,
            self.trnsysId,
            self.diameterInCm,
            self.uValueInWPerM2K,
            self.lengthInM,
            self.shallCreateTrnsysUnit,
        )

        dictName = "Connection-"
        return dictName, connectionModel.to_dict()

    def decode(self, i):
        model = _model.ConnectionModel.from_dict(i)

        self.id = model.id
        self.connId = model.connectionId
        self.trnsysId = model.trnsysId
        self.setDisplayName(model.name)

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)

        self.diameterInCm = model.diameterInCm
        self.uValueInWPerM2K = model.uValueInWPerM2K
        self.lengthInM = model.lengthInM

        self.shallCreateTrnsysUnit = model.shallCreateTrnsysUnit

    def getInternalPiping(self) -> _pi.InternalPiping:
        return _pi.InternalPiping(
            [self.modelPipe], {self.modelPipe.fromPort: self.fromPort, self.modelPipe.toPort: self.toPort}
        )

    def exportPipeAndTeeTypesForTemp(self, startingUnit):  # pylint: disable=too-many-locals, too-many-statements
        inputMfrName = _helpers.getInputMfrName(self, self.modelPipe)
        canonicalMfrName = _mnames.getCanonicalMassFlowVariableName(self, self.modelPipe)

        portItemsWithParent = self._getFromAndToPortsAndParentBlockItems()

        inputTemperatureVariableName = _helpers.getTemperatureVariableName(
            portItemsWithParent[0][1], portItemsWithParent[0][0], _mfn.PortItemType.STANDARD
        )
        revInputTemperatureVariableName = _helpers.getTemperatureVariableName(
            portItemsWithParent[1][1], portItemsWithParent[1][0], _mfn.PortItemType.STANDARD
        )

        outputTemperatureName = _temps.getTemperatureVariableName(self, self.modelPipe)

        unitNumber = startingUnit

        if not self.shallCreateTrnsysUnit:
            unitText = self._getPassThroughPipeDefinition(
                startingUnit,
                inputMfrName,
                canonicalMfrName,
                inputTemperatureVariableName,
                revInputTemperatureVariableName,
                outputTemperatureName,
            )
            return unitText, unitNumber + 1

        unitText = self._getTrnsysUnitDefinition(
            unitNumber,
            inputMfrName,
            canonicalMfrName,
            inputTemperatureVariableName,
            revInputTemperatureVariableName,
            outputTemperatureName,
        )

        nextUnitNumber = unitNumber + 1

        return unitText, nextUnitNumber

    def _getPassThroughPipeDefinition(
        self,
        unitNumber,
        inputMfrName,
        canonicalMfrName,
        inputTemperatureVariableName,
        revInputTemperatureVariableName,
        outputTemperatureName,
    ):
        outputTemperatureUnit = _helpers.getIfThenElseUnit(
            unitNumber,
            outputTemperatureName,
            canonicalMfrName,
            inputTemperatureVariableName,
            revInputTemperatureVariableName,
        )

        unitText = f"""\
! {self.displayName}
EQUATIONS 1
{canonicalMfrName} = {inputMfrName}
{outputTemperatureUnit}

"""
        return unitText

    def _getTrnsysUnitDefinition(  # pylint: disable=too-many-locals
        self,
        unitNumber,
        inputMfrName,
        canonicalMfrName,
        inputTemperatureVariableName,
        revInputTemperatureVariableName,
        outputTemperatureName,
    ):
        loop = self._editor.hydraulicLoops.getLoopForExistingConnection(self)
        densityVar = _names.getDensityName(loop.name.value)
        specHeatVar = _names.getHeatCapacityName(loop.name.value)
        lengthInM = _getConvertedValueOrName(self.lengthInM)
        diameterInM = _getConvertedValueOrName(self.diameterInCm, 1 / 100)
        uValueInkJPerHourM2K = _getConvertedValueOrName(self.uValueInWPerM2K, 60 * 60 / 1000)
        uValueInSIUnitsComment = (
            f" (= {self.uValueInWPerM2K} W/(m^2*K))" if isinstance(self.uValueInWPerM2K, float) else ""
        )
        convectedHeatFluxName = self.getConvectedHeatFluxVariableName()
        dissipatedHeatFluxName = self.getDissipatedHeatFluxVariableName()
        internalHeatName = self.getInternalHeatVariableName()
        unitText = f"""\
UNIT {unitNumber} TYPE 931
! {self.displayName}
PARAMETERS 6
{diameterInM} ! diameter [m]
{lengthInM} ! length [m]
{uValueInkJPerHourM2K} ! U-value [kJ/(h*m^2*K)] {uValueInSIUnitsComment}
{densityVar} ! density [kg/m^3]
{specHeatVar} ! specific heat [kJ/(kg*K)]
20 ! Initial fluid temperature [deg C]
INPUTS 4
{inputTemperatureVariableName} ! input flow temperature [deg C]
{inputMfrName} ! input mass flow [kg/h]
TRoomStore ! ambient temperature [deg C]
{revInputTemperatureVariableName} ! reverse flow input temperature [deg C]
***Initial values
20 0.0 20 20

EQUATIONS 5
{outputTemperatureName} = [{unitNumber},1] ! Output flow temperature [deg C]
{dissipatedHeatFluxName} = [{unitNumber},3]/3600 ! Dissipated heat [kW]
{convectedHeatFluxName} = [{unitNumber},4]/3600 ! Convected heat [kW]
{internalHeatName} = [{unitNumber},5] ! Accumulated internal energy since start of simulation [kJ]
{canonicalMfrName} = {inputMfrName}

"""
        return unitText

    def getConvectedHeatFluxVariableName(self) -> str:
        return f"P{self.displayName}Conv_kW"

    def getDissipatedHeatFluxVariableName(self) -> str:
        return f"P{self.displayName}_kW"

    def getInternalHeatVariableName(self) -> str:
        return f"P{self.displayName}Int_kJ"

    def _getFromAndToPortsAndParentBlockItems(
        self,
    ) -> _tp.Tuple[
        _tp.Tuple[_pib.PortItemBase, _pi.HasInternalPiping], _tp.Tuple[_pib.PortItemBase, _pi.HasInternalPiping]
    ]:
        isToPortValveOutput = (
            isinstance(self.toPort.parent, _tventil.TVentil) and self.fromPort in self.toPort.parent.outputs
        )
        if isToPortValveOutput:
            return (self.toPort, self.toPort.parent), (self.fromPort, self.fromPort.parent)

        return (self.fromPort, self.fromPort.parent), (self.toPort, self.toPort.parent)

    def setMassFlowAndTemperature(self, massFlow: float, temperature: float) -> None:
        label = _mfl.getFormattedMassFlowAndTemperature(massFlow, temperature)
        for segment in self.segments:
            segment.labelMass.setPlainText(label)


def _getConvertedValueOrName(valueOrName: _values.Value, conversionFactor=1.0) -> _tp.Union[float, str]:
    if isinstance(valueOrName, _values.Variable):
        return valueOrName.name

    value = valueOrName

    return value * conversionFactor
