from __future__ import annotations

import dataclasses as _dc
import enum as _enum
import typing as _tp
import uuid as _uuid

import PyQt5.QtWidgets as _qtw
import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.doublePipeSegmentItem as _dpsi
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps
from . import _massFlowLabels as _mfl


@_dc.dataclass
class _EnergyBalanceVariable:
    name: str
    outputNumber: int
    conversionFactor: str
    comment: str


class EnergyBalanceVariables(_enum.Enum):
    PIPE_TO_GRAVEL = "Diss"
    CONVECTED = "Conv"
    PIPE_INTERNAL_CHANGE = "Int"
    COLD_TO_HOT = "Exch"
    GRAVEL_TO_SOIL = "GrSl"
    SOIL_TO_FAR_FIELD = "SlFf"
    SOIL_INTERNAL_CHANGE = "SlInt"


class DoublePipeConnection(_cb.ConnectionBase):
    def __init__(self, fromPort: _dppi.DoublePipePortItem, toPort: _dppi.DoublePipePortItem, parent):
        super().__init__(fromPort, toPort, parent)

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.idGen.getTrnsysID())

        self._updateModels(self.displayName)

    @property
    def fromPort(self) -> _dppi.DoublePipePortItem:
        assert isinstance(self._fromPort, _dppi.DoublePipePortItem)
        return self._fromPort

    @property
    def toPort(self) -> _dppi.DoublePipePortItem:
        assert isinstance(self._toPort, _dppi.DoublePipePortItem)
        return self._toPort

    def getModelPipe(self, portItemType: _mfn.PortItemType) -> _mfn.Pipe:
        if portItemType == _mfn.PortItemType.COLD:
            return self.coldModelPipe

        if portItemType == _mfn.PortItemType.HOT:
            return self.hotModelPipe

        raise ValueError(f"Don't have a model pipe of type {portItemType}.")

    def _createSegmentItem(self, startNode, endNode):
        return _dpsi.DoublePipeSegmentItem(startNode, endNode, self)

    def getRadius(self):
        rad = 4
        return rad

    def createDeleteUndoCommand(self, parentCommand: _tp.Optional[_qtw.QUndoCommand] = None) -> _qtw.QUndoCommand:
        undoCommand = DeleteDoublePipeConnectionCommand(self, parentCommand)
        return undoCommand

    def encode(self):
        if len(self.segments) > 0:
            labelPos = self.segments[0].label.pos().x(), self.segments[0].label.pos().y()
            labelMassPos = self.segments[0].labelMass.pos().x(), self.segments[0].labelMass.pos().y()
        else:
            self.logger.debug("This connection has no segment")
            defaultPos = self.fromPort.pos().x(), self.fromPort.pos().y()  # pylint: disable = duplicate-code # 1
            labelPos = defaultPos
            labelMassPos = defaultPos

        corners = []
        for corner in self.getCorners():
            cornerTupel = (corner.pos().x(), corner.pos().y())
            corners.append(cornerTupel)

        doublePipeConnectionModel = DoublePipeConnectionModel(
            self.connId,
            self.displayName,
            self.id,
            self.childIds,
            corners,
            labelPos,
            labelMassPos,
            self.fromPort.id,
            self.toPort.id,
            self.trnsysId,
        )

        dictName = "Connection-"
        return dictName, doublePipeConnectionModel.to_dict()

    def decode(self, i):
        model = DoublePipeConnectionModel.from_dict(i)

        self.id = model.id
        self.connId = model.connectionId
        self.trnsysId = model.trnsysId
        self.childIds = model.childIds
        self.setDisplayName(model.name)

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)

    def getInternalPiping(self) -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self.coldModelPipe.fromPort: self.toPort,
            self.coldModelPipe.toPort: self.fromPort,
        }

        hotModelPortItemsToGraphicalPortItem = {
            self.hotModelPipe.fromPort: self.fromPort,
            self.hotModelPipe.toPort: self.toPort,
        }

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
        return _ip.InternalPiping([self.coldModelPipe, self.hotModelPipe], modelPortItemsToGraphicalPortItem)

    def exportPipeAndTeeTypesForTemp(
        self, startingUnit: int
    ) -> _tp.Tuple[str, int]:  # pylint: disable=too-many-locals,too-many-statements
        unitNumber = startingUnit

        headerAndParameters = self._getHeaderAndParameters(unitNumber)
        inputs = self._getInputs()
        equations = self._getEquations(unitNumber)

        unitText = headerAndParameters + inputs + equations
        nextUnitNumber = unitNumber + 1

        return unitText, nextUnitNumber

    def _getHeaderAndParameters(self, unitNumber: int) -> str:
        headerAndParameters = f"""\
UNIT {unitNumber} TYPE 9511
! {self.displayName}
PARAMETERS 36
****** pipe and soil properties ******
dpLength                                ! Length of buried pipe, m
dpDiamIn                                ! Inner diameter of pipes, m
dpDiamOut                               ! Outer diameter of pipes, m
dpLambda                                ! Thermal conductivity of pipe material, kJ/(h*m*K)
dpDepth                                 ! Buried pipe depth, m
dpDiamCase                              ! Diameter of casing material, m
dpLambdaFill                            ! Thermal conductivity of fill insulation, kJ/(h*m*K)
dpDistPtoP                              ! Center-to-center pipe spacing, m
dpLambdaGap                             ! Thermal conductivity of gap material, kJ/(h*m*K)
dpGapThick                              ! Gap thickness, m
****** fluid properties ******
dpRhoFlu                                ! Density of fluid, kg/m^3
dpLambdaFl                              ! Thermal conductivity of fluid, kJ/(h*m*K)
dpCpFl                                  ! Specific heat of fluid, kJ/(kg*K)
dpViscFl                                ! Viscosity of fluid, kg/(m*h)
****** initial conditions ******
dpTIniCold                              ! Initial fluid temperature - Pipe cold, deg C
dpTIniHot                               ! Initial fluid temperature - Pipe hot, deg C
****** thermal properties soil ******
dpLamdaSl                               ! Thermal conductivity of soil, kJ/(h*m*K)
dpRhoSl                                 ! Density of soil, kg/m^3
dpCpSl                                  ! Specific heat of soil, kJ/(kg*K)
****** general temperature dependency (dependent on weather data) ******
TambAvg                                 ! Average surface temperature, deg C
dTambAmpl                               ! Amplitude of surface temperature, deg C
ddTcwOffset                             ! Days of minimum surface temperature
****** definition of nodes ******
dpNrFlNds                               ! Number of fluid nodes
dpNrSlRad                               ! Number of radial soil nodes
dpNrSlAx                                ! Number of axial soil nodes
dpNrSlCirc                              ! Number of circumferential soil nodes
dpRadNdDist                             ! Radial distance of node 1, m
dpRadNdDist                             ! Radial distance of node 2, m
dpRadNdDist                             ! Radial distance of node 3, m
dpRadNdDist                             ! Radial distance of node 4, m
dpRadNdDist                             ! Radial distance of node 5, m
dpRadNdDist                             ! Radial distance of node 6, m
dpRadNdDist                             ! Radial distance of node 7, m
dpRadNdDist                             ! Radial distance of node 8, m
dpRadNdDist                             ! Radial distance of node 9, m
dpRadNdDist                             ! Radial distance of node 10, m

"""
        return headerAndParameters

    def _getInputs(self) -> str:
        coldTemperatureName = _helpers.getTemperatureVariableName(
            self.toPort.parent, self.toPort, _mfn.PortItemType.COLD
        )
        coldMfrName = _helpers.getInputMfrName(self, self.coldModelPipe)
        coldRevTemperatureName = _helpers.getTemperatureVariableName(
            self.fromPort.parent, self.fromPort, _mfn.PortItemType.COLD
        )
        hotTemperatureName = _helpers.getTemperatureVariableName(
            self.fromPort.parent, self.fromPort, _mfn.PortItemType.HOT
        )
        hotMfrName = _helpers.getInputMfrName(self, self.hotModelPipe)
        hotRevTemperatureName = _helpers.getTemperatureVariableName(
            self.toPort.parent, self.toPort, _mfn.PortItemType.HOT
        )
        inputs = f"""\
INPUTS 6
{coldTemperatureName} ! Inlet fluid temperature - cold pipe, deg C
{coldMfrName} ! Inlet fluid flow rate - cold pipe, kg/h
{coldRevTemperatureName} ! ! Other side of pipe - cold pipe, deg C
{hotTemperatureName} ! Inlet fluid temperature - hot pipe, deg C
{hotMfrName} ! Inlet fluid flow rate - hot pipe, kg/h
{hotRevTemperatureName} ! ! Other side of pipe - hot pipe, deg C
*** initial values
dpTIniCold
0
dpTIniCold
dpTIniHot
0
dpTIniHot

"""
        return inputs

    def _getEquations(self, unitNumber: int) -> str:
        energyBalanceVariables = self._getEnergyBalanceVariables()
        formattedEnergyBalanceVariables = "\n".join(
            f"{v.name} = [{unitNumber},{v.outputNumber}]*{v.conversionFactor} ! {v.comment}"
            for v in energyBalanceVariables
        )
        coldMfrName = _helpers.getInputMfrName(self, self.coldModelPipe)
        hotMfrName = _helpers.getInputMfrName(self, self.hotModelPipe)
        equations = f"""\
EQUATIONS {4 + len(energyBalanceVariables)}
{_temps.getTemperatureVariableName(self, self.coldModelPipe)} = [{unitNumber},1]  ! Outlet fluid temperature, deg C
{_mnames.getCanonicalMassFlowVariableName(self, self.coldModelPipe)} = {coldMfrName}  ! Outlet mass flow rate, kg/h

{_temps.getTemperatureVariableName(self, self.hotModelPipe)} = [{unitNumber},3]  ! Outlet fluid temperature, deg C
{_mnames.getCanonicalMassFlowVariableName(self, self.hotModelPipe)} = {hotMfrName}  ! Outlet mass flow rate, kg/h

{formattedEnergyBalanceVariables}

"""
        return equations

    def _getEnergyBalanceVariables(self) -> _tp.Sequence[_EnergyBalanceVariable]:
        return [
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.CONVECTED,
                _mfn.PortItemType.COLD,
                7,
                "Convected heat [kW]",
                conversionFactor="-1*1/3600",
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.PIPE_INTERNAL_CHANGE,
                _mfn.PortItemType.COLD,
                9,
                "Change in fluid's internal heat content compared to previous time step [kW]",
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.PIPE_TO_GRAVEL,
                _mfn.PortItemType.COLD,
                11,
                "Dissipated heat to casing (aka gravel) [kW]",
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.CONVECTED,
                _mfn.PortItemType.HOT,
                8,
                "Convected heat [kW]",
                conversionFactor="-1*1/3600",
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.PIPE_INTERNAL_CHANGE,
                _mfn.PortItemType.HOT,
                10,
                "Change in fluid's internal heat content compared to previous time step [kW]",
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.PIPE_TO_GRAVEL,
                _mfn.PortItemType.HOT,
                12,
                "Dissipated heat to casing (aka gravel) [kW]",
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.COLD_TO_HOT, None, 13, "Dissipated heat from cold pipe to hot pipe [kW]"
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.GRAVEL_TO_SOIL, None, 14, "Dissipated heat from gravel to soil [kW]"
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.SOIL_TO_FAR_FIELD, None, 15, 'Dissipated heat from soil to "far field" [kW]'
            ),
            self._getEnergyBalanceVariable(
                EnergyBalanceVariables.SOIL_INTERNAL_CHANGE,
                None,
                16,
                "Change in soil's internal heat content compared to previous time step [kW]",
            ),
        ]

    def _getEnergyBalanceVariable(
        self,
        variable: EnergyBalanceVariables,
        portItemType: _tp.Optional[_mfn.PortItemType],
        outputNumber: int,
        comment: str,
        conversionFactor: str = "1/3600",
    ) -> _EnergyBalanceVariable:
        variableName = self.getEnergyBalanceVariableName(variable, portItemType)
        return _EnergyBalanceVariable(variableName, outputNumber, conversionFactor, comment)

    def getEnergyBalanceVariableName(
        self,
        variable: EnergyBalanceVariables,
        portItemType: _tp.Optional[_mfn.PortItemType] = None,
    ) -> str:
        prefix = self._getEnergyBalanceVariablePrefix(portItemType)
        variableName = f"{prefix}{variable.value}"
        return variableName

    def _getEnergyBalanceVariablePrefix(self, portItemType: _tp.Optional[_mfn.PortItemType]):
        if not portItemType:
            return self.displayName

        assert portItemType in [_mfn.PortItemType.COLD, _mfn.PortItemType.HOT]
        pipeName = self.coldModelPipe.name if portItemType == _mfn.PortItemType.COLD else self.hotModelPipe.name
        return f"{self.displayName}{pipeName}"

    @staticmethod
    def _addComment(firstColumn, comment):
        spacing = 40
        return str(firstColumn).ljust(spacing) + comment + "\n"

    def _updateModels(self, newDisplayName: str):
        coldFromPort: _mfn.PortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
        coldToPort: _mfn.PortItem = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
        self.coldModelPipe = _mfn.Pipe(coldFromPort, coldToPort, name="Cold")

        hotFromPort: _mfn.PortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
        hotToPort: _mfn.PortItem = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
        self.hotModelPipe = _mfn.Pipe(hotFromPort, hotToPort, name="Hot")

    def setMassFlowAndTemperature(
        self, coldMassFlow: float, coldTemperature: float, hotMassFlow: float, hotTemperature: float
    ) -> None:
        formattedColdMassFlowAndTemperature = _mfl.getFormattedMassFlowAndTemperature(coldMassFlow, coldTemperature)
        formattedHotMassFlowAndTemperature = _mfl.getFormattedMassFlowAndTemperature(hotMassFlow, hotTemperature)
        labelText = f"""\
Cold: {formattedColdMassFlowAndTemperature}
Hot: {formattedHotMassFlowAndTemperature}
"""
        for segment in self.segments:
            segment.labelMass.setPlainText(labelText)


class DeleteDoublePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(
        self, doublePipeConnection: DoublePipeConnection, parentCommand: _tp.Optional[_qtw.QUndoCommand] = None
    ) -> None:
        super().__init__("Delete double pipe connection", parentCommand)
        self._connection = doublePipeConnection
        self._fromPort = self._connection.fromPort
        self._toPort = self._connection.toPort
        self._editor = self._connection.parent

    def undo(self):
        self._connection = DoublePipeConnection(self._fromPort, self._toPort, self._editor)

    def redo(self):
        self._connection.deleteConn()
        self._connection = None


@_dc.dataclass
class DoublePipeConnectionModel(_ser.UpgradableJsonSchemaMixinVersion0):  # pylint: disable=too-many-instance-attributes
    connectionId: int
    name: str
    id: int  # pylint: disable=invalid-name
    childIds: _tp.List[int]
    segmentsCorners: _tp.List[_tp.Tuple[float, float]]
    labelPos: _tp.Tuple[float, float]
    massFlowLabelPos: _tp.Tuple[float, float]
    fromPortId: int
    toPortId: int
    trnsysId: int

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,  # pylint: disable=duplicate-code  # 1
        validate=True,
        validate_enums: bool = True,
    ) -> "DoublePipeConnectionModel":
        data.pop(".__ConnectionDict__")
        doublePipeConnectionModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(DoublePipeConnectionModel, doublePipeConnectionModel)

    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code # 1
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__ConnectionDict__"] = True
        return data

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("0810c9ea-85df-4431-bb40-3190c25c9161")
