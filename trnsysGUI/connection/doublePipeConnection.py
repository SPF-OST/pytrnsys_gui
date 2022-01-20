from __future__ import annotations

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import PyQt5.QtWidgets as _qtw

import dataclasses_jsonschema as _dcj

import massFlowSolver.networkModel as _mfn
import trnsysGUI.serialization as _ser
from massFlowSolver import InternalPiping  # type: ignore[attr-defined]
from trnsysGUI.PortItemBase import PortItemBase  # type: ignore[attr-defined]
from trnsysGUI.connection.connectionBase import ConnectionBase  # type: ignore[attr-defined]
from trnsysGUI.doublePipeSegmentItem import DoublePipeSegmentItem
from trnsysGUI.doublePipeModelPortItems import ColdPortItem, HotPortItem

class DoublePipeConnection(ConnectionBase):
    def __init__(self, fromPort: PortItemBase, toPort: PortItemBase, parent):
        super().__init__(fromPort, toPort, parent)

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.idGen.getTrnsysID())

    def _createSegmentItem(self, startNode, endNode):
        return DoublePipeSegmentItem(startNode, endNode, self)

    def getRadius(self):
        rad = 4
        return rad

    def deleteConnCom(self):
        command = DeleteDoublePipeConnectionCommand(self)
        self.parent.parent().undoStack.push(command)

    def encode(self):
        if len(self.segments) > 0:
            labelPos = self.segments[0].label.pos().x(), self.segments[0].label.pos().y()
            labelMassPos = self.segments[0].labelMass.pos().x(), self.segments[0].labelMass.pos().y()
        else:
            self.logger.debug("This connection has no segment")
            defaultPos = self.fromPort.pos().x(), self.fromPort.pos().y()
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
        self.setName(model.name)

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)

    def getInternalPiping(self) -> InternalPiping:
        coldFromPort: _mfn.PortItem = ColdPortItem("Cold Input", _mfn.PortItemType.INPUT)
        coldToPort: _mfn.PortItem = ColdPortItem("Cold Output", _mfn.PortItemType.OUTPUT)
        coldPipe = _mfn.Pipe(self.displayName + "Cold", self.childIds[0], coldFromPort, coldToPort)
        coldModelPortItemsToGraphicalPortItem = {coldFromPort: self.toPort, coldToPort: self.fromPort}

        hotFromPort: _mfn.PortItem = HotPortItem("Hot Input", _mfn.PortItemType.INPUT)
        hotToPort: _mfn.PortItem = HotPortItem("Hot Output", _mfn.PortItemType.OUTPUT)
        hotPipe = _mfn.Pipe(self.displayName + "Hot", self.childIds[1], hotFromPort, hotToPort)
        hotModelPortItemsToGraphicalPortItem = {hotFromPort: self.fromPort, hotToPort: self.toPort}

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
        return InternalPiping([coldPipe, hotPipe], modelPortItemsToGraphicalPortItem)

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

        openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
        assert len(openLoops) == 2
        coldOpenLoop = openLoops[0]
        hotOpenLoop = openLoops[1]

        unitText += "INPUTS " + str(inputNumbers) + "\n"
        unitText += self._getInputs(nodesToIndices, coldOpenLoop, "Cold")
        unitText += self._getInputs(nodesToIndices, hotOpenLoop, "Hot")

        unitText += "***Initial values\n"
        unitText += initialValueS + "\n\n"

        unitText += "EQUATIONS " + str(equationNr) + "\n"
        unitText += self._getEquations(eqConst1, eqConst7, coldOpenLoop, nodesToIndices, unitNumber, "Cold")
        unitText += self._getEquations(eqConst3, eqConst8, hotOpenLoop, nodesToIndices, unitNumber, "Hot")

        unitNumber += 1
        unitText += "\n"

        return unitText, unitNumber

    def _getInputs(self, nodesToIndices, openLoop, temperature):
        realNode = self._getSingleNode(openLoop)

        outputVariables = realNode.serialize(nodesToIndices).outputVariables
        outputVariable = outputVariables[0]

        portItemsWithParent = self._getPortItemsWithParent()
        assert len(portItemsWithParent) == 2

        parent = portItemsWithParent[0][1]
        firstColumn = f"T{parent.displayName}{temperature}"
        unitText = self._addComment(firstColumn, f"! Inlet fluid temperature - Pipe {temperature}, deg C")

        firstColumn = f"{outputVariable.name}"
        unitText += self._addComment(firstColumn, f"! Inlet fluid flow rate - Pipe {temperature}, kg/h")

        parent = portItemsWithParent[1][1]
        firstColumn = f"T{parent.displayName}{temperature}"
        unitText += self._addComment(firstColumn, "! Other side of pipe, deg C")

        return unitText

    @staticmethod
    def _getSingleNode(openLoop):
        assert len(openLoop.realNodes) == 1
        realNode = openLoop.realNodes[0]
        return realNode

    def _getEquations(self, equationConstant1, equationConstant2, openLoop, nodesToIndices, unitNumber, temperature):
        realNode = self._getSingleNode(openLoop)
        outputVariables = realNode.serialize(nodesToIndices).outputVariables
        outputVariable = outputVariables[0]

        firstColumn = (
            "T" + self.displayName + temperature + " = [" + str(unitNumber) + "," + str(equationConstant1) + "]"
        )
        unitText = self._addComment(
            firstColumn, f"! {equationConstant1}: Outlet fluid temperature pipe {temperature}, deg C"
        )
        firstColumn = f"Mfr{self.displayName}{temperature} = {outputVariable.name}"
        unitText += self._addComment(firstColumn, f"! Outlet mass flow rate pipe {temperature}, kg/h")
        firstColumn = f"P{self.displayName}{temperature}_kW = [{unitNumber},{equationConstant2}]/3600"
        unitText += self._addComment(firstColumn, f"! {equationConstant2}: Delivered energy pipe {temperature}, kW")
        return unitText

    @staticmethod
    def _addComment(firstColumn, comment):
        spacing = 40
        return str(firstColumn).ljust(spacing) + comment + "\n"


class DeleteDoublePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(self, conn):
        super().__init__("Delete double pipe connection")
        self._connection = conn
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
