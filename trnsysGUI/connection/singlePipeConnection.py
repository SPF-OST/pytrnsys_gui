from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.TVentil as _tventil
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.deleteSinglePipeConnectionCommand as _dspc
import trnsysGUI.connection.hydraulicExport.common as _hecom
import trnsysGUI.connection.hydraulicExport.singlePipe.createExportHydraulicSinglePipeConnection as _cehc
import trnsysGUI.connection.hydraulicExport.singlePipe.dummy as _he
import trnsysGUI.connection.hydraulicExport.singlePipe.singlePipeConnection as _hespc
import trnsysGUI.connection.singlePipeConnectionModel as _model
import trnsysGUI.connection.singlePipeDefaultValues as _defaults
import trnsysGUI.connection.values as _values
import trnsysGUI.globalNames as _gnames
import trnsysGUI.hydraulicLoops.names as _names
import trnsysGUI.internalPiping as _pi
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.names.undo as _nu
import trnsysGUI.segments.singlePipeSegmentItem as _spsi
import trnsysGUI.singlePipePortItem as _sppi
import trnsysGUI.temperatures as _temps
from . import _massFlowLabels as _mfl

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class SinglePipeConnection(_cb.ConnectionBase):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        displayName: str,
        fromPort: _sppi.SinglePipePortItem,
        toPort: _sppi.SinglePipePortItem,
        parent: _ed.Editor,  # type: ignore[name-defined]
    ):
        shallBeSimulated = True
        super().__init__(displayName, fromPort, toPort, shallBeSimulated, _defaults.DEFAULT_LENGTH_IN_M, parent)

        self.diameterInCm: _values.Value = _defaults.DEFAULT_DIAMETER_IN_CM
        self.uValueInWPerM2K: _values.Value = _defaults.DEFAULT_U_VALUE_IN_W_PER_M2_K

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
        undoNamingHelper = _nu.UndoNamingHelper.create(self._editor.namesManager)

        hydraulicLoopsData = _dspc.HydraulicLoopsData(
            self._editor.hydraulicLoops,
            self._editor.fluids.fluids,
            self._editor.fluids.WATER,
        )

        undoCommand = _dspc.DeleteSinglePipeConnectionCommand(
            self,
            undoNamingHelper,
            hydraulicLoopsData,
            self._editor.diagramScene,
            parentCommand,
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
            self.shallBeSimulated,
        )

        dictName = "Connection-"
        return dictName, connectionModel.to_dict()

    def decode(self, i):
        model = _model.ConnectionModel.from_dict(i)

        self.id = model.id
        self.connId = model.connectionId
        self.trnsysId = model.trnsysId
        self.setDisplayName(model.name)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)

        self.diameterInCm = model.diameterInCm
        self.uValueInWPerM2K = model.uValueInWPerM2K
        self.lengthInM = model.lengthInM

        self.shallBeSimulated = model.shallBeSimulated

        if len(model.segmentsCorners) > 0:
            self._loadSegments(model.segmentsCorners)

    def getInternalPiping(self) -> _pi.InternalPiping:
        return _pi.InternalPiping(
            [self.modelPipe], {self.modelPipe.fromPort: self.fromPort, self.modelPipe.toPort: self.toPort}
        )

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        unitNumber = startingUnit

        exportHydraulicConnection = self._createExportHydraulicConnection()

        if not self.shallBeSimulated:
            return _he.exportDummyConnection(exportHydraulicConnection, unitNumber)

        return self._exportSimulatedPipe(exportHydraulicConnection, unitNumber)

    def _exportSimulatedPipe(self, exportHydraulicConnection, unitNumber) -> _tp.Tuple[str, int]:

        canonicalMfrName = _mnames.getCanonicalMassFlowVariableName(
            componentDisplayName=exportHydraulicConnection.displayName, pipeName=None
        )

        outputTemperatureName = _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False,
            componentDisplayName=exportHydraulicConnection.displayName,
            nodeName=None,
        )

        exportPipe = exportHydraulicConnection.pipe
        unitText = self._getSimulatedPipeUnitText(
            unitNumber,
            exportPipe.inputPort.massFlowRateVariableName,
            canonicalMfrName,
            exportPipe.inputPort.inputTemperatureVariableName,
            exportPipe.outputPort.inputTemperatureVariableName,
            outputTemperatureName,
        )

        nextUnitNumber = unitNumber + 1

        return unitText, nextUnitNumber

    def _createExportHydraulicConnection(self) -> _hespc.ExportHydraulicSinglePipeConnection:
        hydraulicConnection = _cehc.HydraulicSinglePipeConnection(
            self.displayName,
            _hecom.getAdjacentBlockItem(self.fromPort),
            _hecom.getAdjacentBlockItem(self.toPort),
            self.modelPipe,
        )

        exportHydraulicConnection = _cehc.createExportHydraulicConnection(hydraulicConnection)

        return exportHydraulicConnection

    def _getSimulatedPipeUnitText(  # pylint: disable=too-many-locals
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
        lengthInM = _values.getConvertedValueOrName(self.lengthInM)
        diameterInM = _values.getConvertedValueOrName(self.diameterInCm, 1 / 100)
        uValueInkJPerHourM2K = _values.getConvertedValueOrName(self.uValueInWPerM2K, 60 * 60 / 1000)
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
{_gnames.SinglePipes.INITIAL_TEMPERATURE} ! Initial fluid temperature [deg C]
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
