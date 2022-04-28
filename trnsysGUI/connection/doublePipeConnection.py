from __future__ import annotations

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import PyQt5.QtWidgets as _qtw
import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.doublePipeModelPortItems as _dpmpi
import trnsysGUI.doublePipeSegmentItem as _dpsi
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.connectorsAndPipesExportHelpers as _helpers


class DoublePipeConnection(_cb.ConnectionBase):
    def __init__(self, fromPort: _dppi.DoublePipePortItem, toPort: _dppi.DoublePipePortItem, parent):
        super().__init__(fromPort, toPort, parent)

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.idGen.getTrnsysID())

        self._updateModelPipes(self.displayName)

    def setDisplayName(self, newName: str) -> None:
        super().setDisplayName(newName)
        self._updateModelPipes(newName)

    @property
    def fromPort(self) -> _dppi.DoublePipePortItem:
        assert isinstance(self._fromPort, _dppi.DoublePipePortItem)
        return self._fromPort

    @property
    def toPort(self) -> _dppi.DoublePipePortItem:
        assert isinstance(self._toPort, _dppi.DoublePipePortItem)
        return self._toPort

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

    def getInternalPiping(self) -> _mfs.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self._coldPipe.fromPort: self.toPort,
            self._coldPipe.toPort: self.fromPort,
        }

        hotModelPortItemsToGraphicalPortItem = {
            self._hotPipe.fromPort: self.fromPort,
            self._hotPipe.toPort: self.toPort
        }

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
        return _mfs.InternalPiping([self._coldPipe, self._hotPipe], modelPortItemsToGraphicalPortItem)

    def exportPipeAndTeeTypesForTemp(self, startingUnit):  # pylint: disable=too-many-locals,too-many-statements
        unitNumber = startingUnit
        typeNr2 = 9511  # Temperature calculation from a pipe

        unitText = ""
        commentStars = 6 * "*"

        parameterNumber = 35
        inputNumbers = 6

        eqConst1 = 1
        eqConst3 = 3
        eqConst7 = 7
        eqConst8 = 8

        # Fixed strings
        initialValueS = "15.0 0.0 15.0 15.0 0.0 15.0"

        # Momentarily hardcoded
        equationNr = 6

        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
        unitText += "!" + self.displayName + "\n"

        unitText += "PARAMETERS " + str(parameterNumber) + "\n"
        unitText += commentStars + " pipe and soil properties " + commentStars + "\n"
        unitText += self._addComment("dpLength", "! Length of buried pipe, m")
        unitText += self._addComment("dpDiamIn", "! Inner diameter of pipes, m")
        unitText += self._addComment("dpDiamOut", "! Outer diameter of pipes, m")
        unitText += self._addComment("dpLambda", "! Thermal conductivity of pipe material, kJ/(h*m*K)")
        unitText += self._addComment("dpDepth", "! Buried pipe depth, m")
        unitText += self._addComment("dpFlowMode", "! Direction of second pipe flow: 1 = same, 2 = opposite")
        unitText += self._addComment("dpDiamCase", "! Diameter of casing material, m")
        unitText += self._addComment("dpLambdaFill", "! Thermal conductivity of fill insulation, kJ/(h*m*K)")
        unitText += self._addComment("dpDistPtoP", "! Center-to-center pipe spacing, m")
        unitText += self._addComment("dpLambdaGap", "! Thermal conductivity of gap material, kJ/(h*m*K)")
        unitText += self._addComment("dpGapThick", "! Gap thickness, m")

        unitText += commentStars + " fluid properties " + commentStars + "\n"
        unitText += self._addComment("dpRhoFlu", "! Density of fluid, kg/m^3")
        unitText += self._addComment("dpLambdaFl", "! Thermal conductivity of fluid, kJ/(h*m*K)")
        unitText += self._addComment("dpCpFl", "! Specific heat of fluid, kJ/(kg*K)")
        unitText += self._addComment("dpViscFl", "! Viscosity of fluid, kg/(m*h)")

        unitText += commentStars + " initial conditions " + commentStars + "\n"
        unitText += self._addComment("dpTIniHot", "! Initial fluid temperature - Pipe hot, deg C")
        unitText += self._addComment("dpTIniCold", "! Initial fluid temperature - Pipe cold, deg C")

        unitText += commentStars + " thermal properties soil " + commentStars + "\n"
        unitText += self._addComment("dpLamdaSl", "! Thermal conductivity of soil, kJ/(h*m*K)")
        unitText += self._addComment("dpRhoSl", "! Density of soil, kg/m^3")
        unitText += self._addComment("dpCpSl", "! Specific heat of soil, kJ/(kg*K)")

        unitText += commentStars + " general temperature dependency (dependent on weather data) " + commentStars + "\n"
        unitText += self._addComment("TambAvg", "! Average surface temperature, deg C")
        unitText += self._addComment("dTambAmpl", "! Amplitude of surface temperature, deg C")
        unitText += self._addComment("ddTcwOffset", "! Days of minimum surface temperature")

        unitText += commentStars + " definition of nodes " + commentStars + "\n"
        unitText += self._addComment("dpNrFlNds", "! Number of fluid nodes")
        unitText += self._addComment("dpNrSlRad", "! Number of radial soil nodes")
        unitText += self._addComment("dpNrSlAx", "! Number of axial soil nodes")
        unitText += self._addComment("dpNrSlCirc", "! Number of circumferential soil nodes")
        unitText += self._addComment("dpRadNdDist", "! Radial distance of node 1, m")
        unitText += self._addComment("dpRadNdDist", "! Radial distance of node 2, m")
        unitText += self._addComment("dpRadNdDist", "! Radial distance of node 3, m")
        unitText += self._addComment("dpRadNdDist", "! Radial distance of node 4, m")
        unitText += self._addComment("dpRadNdDist", "! Radial distance of node 5, m")
        unitText += self._addComment("dpRadNdDist", "! Radial distance of node 6, m")
        unitText += self._addComment("dpRadNdDist", "! Radial distance of node 7, m")
        unitText += self._addComment("dpRadNdDist", "! Radial distance of node 8, m")

        unitText += "INPUTS " + str(inputNumbers) + "\n"
        unitText += self._getInputs("Cold", self._coldPipe, self.toPort, self.fromPort)
        unitText += self._getInputs("Hot", self._hotPipe, self.fromPort, self.toPort)

        unitText += "***Initial values\n"
        unitText += initialValueS + "\n\n"

        unitText += "EQUATIONS " + str(equationNr) + "\n"
        unitText += self._getEquations("Cold", self._coldPipe, eqConst1, eqConst7, unitNumber)
        unitText += self._getEquations("Hot", self._hotPipe, eqConst3, eqConst8, unitNumber)

        unitNumber += 1
        unitText += "\n"

        return unitText, unitNumber

    def _getInputs(
            self,
            temperatureSuffix: str,
            pipe: _mfn.Pipe,
            pipeFromPort: _dppi.DoublePipePortItem,
            pipeToPort: _dppi.DoublePipePortItem
    ) -> str:
        mfrName = _helpers.getMfrName(pipe)

        fromBlockItem = pipeFromPort.parent
        firstColumn = f"T{fromBlockItem.displayName}{temperatureSuffix}"
        unitText = self._addComment(firstColumn, f"! Inlet fluid temperature - Pipe {temperatureSuffix}, deg C")

        firstColumn = f"{mfrName}"
        unitText += self._addComment(firstColumn, f"! Inlet fluid flow rate - Pipe {temperatureSuffix}, kg/h")

        toBlockItem = pipeToPort.parent
        firstColumn = f"T{toBlockItem.displayName}{temperatureSuffix}"
        unitText += self._addComment(firstColumn, "! Other side of pipe, deg C")

        return unitText

    def _getEquations(self, temperatureSuffix: str, pipe: _mfn.Pipe, equationConstant1, equationConstant2, unitNumber):
        firstColumn = (
            f"T{pipe.name} = [{unitNumber},{equationConstant1}]"
        )
        unitText = self._addComment(
            firstColumn, f"! {equationConstant1}: Outlet fluid temperature pipe {temperatureSuffix}, deg C"
        )

        mfrName = _helpers.getMfrName(pipe)
        firstColumn = f"Mfr{pipe.name} = {mfrName}"
        unitText += self._addComment(firstColumn, f"! Outlet mass flow rate pipe {temperatureSuffix}, kg/h")

        firstColumn = f"P{pipe.name}_kW = [{unitNumber},{equationConstant2}]/3600"
        unitText += self._addComment(
            firstColumn, f"! {equationConstant2}: Delivered energy pipe {temperatureSuffix}, kW"
        )

        return unitText

    @staticmethod
    def _addComment(firstColumn, comment):
        spacing = 40
        return str(firstColumn).ljust(spacing) + comment + "\n"

    def _updateModelPipes(self, displayName: str):
        coldFromPort: _mfn.PortItem = _dpmpi.ColdPortItem("Cold Input", _mfn.PortItemType.INPUT)
        coldToPort: _mfn.PortItem = _dpmpi.ColdPortItem("Cold Output", _mfn.PortItemType.OUTPUT)
        self._coldPipe = _mfn.Pipe(displayName + "Cold", self.childIds[0], coldFromPort, coldToPort)

        hotFromPort: _mfn.PortItem = _dpmpi.HotPortItem("Hot Input", _mfn.PortItemType.INPUT)
        hotToPort: _mfn.PortItem = _dpmpi.HotPortItem("Hot Output", _mfn.PortItemType.OUTPUT)
        self._hotPipe = _mfn.Pipe(displayName + "Hot", self.childIds[1], hotFromPort, hotToPort)


class DeleteDoublePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(self, doublePipeConnection: DoublePipeConnection, parentCommand: _qtw.QUndoCommand = None) -> None:
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
