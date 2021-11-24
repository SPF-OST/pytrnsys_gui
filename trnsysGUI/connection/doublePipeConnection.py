from __future__ import annotations

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import massFlowSolver.networkModel as _mfn
import trnsysGUI.serialization as _ser
from massFlowSolver import InternalPiping  # type: ignore[attr-defined]
from trnsysGUI.PortItemBase import PortItemBase  # type: ignore[attr-defined]
from trnsysGUI.connection.connectionBase import ConnectionBase, DeleteConnectionCommandBase  # type: ignore[attr-defined]
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
        command = DeleteDoublePipeConnectionCommand(self, "Delete conn comand")
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
            self.groupName,
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
        self.groupName = "defaultGroup"
        self.setConnToGroup(model.groupName)

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)

    def getInternalPiping(self) -> InternalPiping:
        coldFromPort: _mfn.PortItem = ColdPortItem()
        coldToPort: _mfn.PortItem = ColdPortItem()
        coldPipe = _mfn.Pipe(self.displayName + "Cold", self.childIds[0], coldFromPort, coldToPort)
        coldModelPortItemsToGraphicalPortItem = {coldFromPort: self.toPort, coldToPort: self.fromPort}

        hotFromPort: _mfn.PortItem = HotPortItem()
        hotToPort: _mfn.PortItem = HotPortItem()
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

        # default values
        lPipe = 24.384
        diPipe = 0.02618
        doPipe = 0.03198
        cpPipe = 1.37067
        depthPipe = 3.0
        dirSecondPipe = 1
        dCasing = 0.17526
        condInsulation = 0.14537
        xPipeToPipe = 0.06911
        condCap = 8.722
        dGap = 0.0000

        rhoFluidPipe = 1000.0
        condFluidPipe = 2.2068
        cpFluidPipe = 4.19
        viscFluidPipe = 3.078

        tiniPipeHot = 10.0
        tiniPipeCold = 10.0

        condSoil = 8.722
        rhoSoil = 2500.0
        cpSoil = 0.84

        tSurfArg = 7.96
        amplSurfAvg = 13.32
        dayMinSfT = 36

        nCvFluid = 100
        nCvRad = 8
        nCvAXSoil = 10
        nCvCircSoil = 4
        dRadn1 = 0.0254

        # Fixed strings
        initialValueS = "15.0 0.0 15.0 15.0 0.0 15.0"

        # Momentarily hardcoded
        equationNr = 6

        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
        unitText += "!" + self.displayName + "\n"

        unitText += "PARAMETERS " + str(parameterNumber) + "\n"
        unitText += commentStars + " pipe and soil properties " + commentStars + "\n"
        unitText += self._addComment(lPipe, "! Length of buried pipe")
        unitText += self._addComment(diPipe, "! Inner diameter of pipes")
        unitText += self._addComment(doPipe, "! Outer diameter of pipes")
        unitText += self._addComment(cpPipe, "! Thermal conductivity of pipe material")
        unitText += self._addComment(depthPipe, "! Buried pipe depth")
        unitText += self._addComment(dirSecondPipe, "! Direction of second pipe flow")
        unitText += self._addComment(dCasing, "! Diameter of casing material	")
        unitText += self._addComment(condInsulation, "! Thermal conductivity of fill insulation")
        unitText += self._addComment(xPipeToPipe, "! Center-to-center pipe spacing")
        unitText += self._addComment(condCap, "! Thermal conductivity of gap material")
        unitText += self._addComment(dGap, "! Gap thickness")

        unitText += commentStars + " fluid properties " + commentStars + "\n"
        unitText += self._addComment(rhoFluidPipe, "! Density of fluid")
        unitText += self._addComment(condFluidPipe, "! Thermal conductivity of fluid")
        unitText += self._addComment(cpFluidPipe, "! Specific heat of fluid")
        unitText += self._addComment(viscFluidPipe, "! Viscosity of fluid")

        unitText += commentStars + " initial conditions " + commentStars + "\n"
        unitText += self._addComment(tiniPipeHot, "! Initial fluid temperature - Pipe hot")
        unitText += self._addComment(tiniPipeCold, "! Initial fluid temperature - Pipe cold")

        unitText += commentStars + " thermal properties soil " + commentStars + "\n"
        unitText += self._addComment(condSoil, "! Thermal conductivity of soil")
        unitText += self._addComment(rhoSoil, "! Density of soil")
        unitText += self._addComment(cpSoil, "! Specific heat of soil")

        unitText += commentStars + " general temperature dependency (dependent from weather data) " + commentStars + "\n"
        unitText += self._addComment(tSurfArg, "! Average surface temperature")
        unitText += self._addComment(amplSurfAvg, "! Amplitude of surface temperature")
        unitText += self._addComment(dayMinSfT, "! Day of minimum surface temperature")

        unitText += commentStars + " definition of nodes " + commentStars + "\n"
        unitText += self._addComment(nCvFluid, "! Number of fluid nodes")
        unitText += self._addComment(nCvRad, "! Number of radial soil nodes")
        unitText += self._addComment(nCvAXSoil, "! Number of axial soil nodes")
        unitText += self._addComment(nCvCircSoil, "! Number of circumferential soil nodes")
        unitText += self._addComment(dRadn1, "! Radial distance of node -1")
        unitText += self._addComment(dRadn1, "! Radial distance of node -2")
        unitText += self._addComment(dRadn1, "! Radial distance of node -3")
        unitText += self._addComment(dRadn1, "! Radial distance of node -4")
        unitText += self._addComment(dRadn1, "! Radial distance of node -5")
        unitText += self._addComment(dRadn1, "! Radial distance of node -6")
        unitText += self._addComment(dRadn1, "! Radial distance of node -7")
        unitText += self._addComment(dRadn1, "! Radial distance of node -8")

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
        unitText += self._addComment(firstColumn, f"! Inlet fluid flow rate - Pipe {temperature}, kJ/h")

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
        unitText += self._addComment(firstColumn, f"! {equationConstant2}: Delivered energy pipe {temperature}, kJ/h")
        return unitText

    @staticmethod
    def _addComment(firstColumn, comment):
        spacing = 40
        return str(firstColumn).ljust(spacing) + comment + "\n"


class DeleteDoublePipeConnectionCommand(DeleteConnectionCommandBase):
    def undo(self):
        self.conn = DoublePipeConnection(self.connFromPort, self.connToPort, self.connParent)


@_dc.dataclass
class DoublePipeConnectionModel(_ser.UpgradableJsonSchemaMixinVersion0):
    connectionId: int
    name: str
    id: int
    childIds: _tp.List[int]
    segmentsCorners: _tp.List[_tp.Tuple[float, float]]
    labelPos: _tp.Tuple[float, float]
    massFlowLabelPos: _tp.Tuple[float, float]
    groupName: str
    fromPortId: int
    toPortId: int
    trnsysId: int

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
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
        validate_enums: bool = True,  # pylint: disable=duplicate-code
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__ConnectionDict__"] = True
        return data

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("0810c9ea-85df-4431-bb40-3190c25c9161")
