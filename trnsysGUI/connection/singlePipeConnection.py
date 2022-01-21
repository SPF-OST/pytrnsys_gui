# pylint: skip-file
# type: ignore

from __future__ import annotations

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.serialization as _ser
import trnsysGUI.singlePipeSegmentItem as _spsi
import trnsysGUI.connection.deleteSinglePipeConnectionCommand as _dspc
import trnsysGUI.hydraulicLoops.export as _hle

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class SinglePipeConnection(_cb.ConnectionBase):
    def __init__(self, fromPort: _pib.PortItemBase, toPort: _pib.PortItemBase, parent: _ed.Editor):
        super().__init__(fromPort, toPort, parent)

        self._editor = parent
        self._diameterInCm = ConnectionModel.DEFAULT_DIAMETER_IN_CM
        self._uValueInWPerM2K = ConnectionModel.DEFAULT_U_VALUE_IN_W_PER_M2_K
        self._lengthInM = ConnectionModel.DEFAULT_LENGTH_IN_M

    @property
    def diameterInCm(self) -> float:
        return self._diameterInCm

    @diameterInCm.setter
    def diameterInCm(self, diameterInCm: float) -> None:
        self._diameterInCm = diameterInCm

    @property
    def uValueInWPerM2K(self) -> float:
        return self._uValueInWPerM2K

    @uValueInWPerM2K.setter
    def uValueInWPerM2K(self, uValueInWPerM2K: float) -> None:
        self._uValueInWPerM2K = uValueInWPerM2K

    @property
    def lengthInM(self) -> float:
        return self._lengthInM

    @lengthInM.setter
    def lengthInM(self, lengthInM: float) -> None:
        self._lengthInM = lengthInM

    def _createSegmentItem(self, startNode, endNode):
        return _spsi.SinglePipeSegmentItem(startNode, endNode, self)

    def getRadius(self):
        rad = 2
        return rad

    def editHydraulicLoop(self) -> None:
        self._editor.editHydraulicLoop(self)

    def deleteConnCom(self):
        deleteConnectionCommand = _dspc.DeleteSinglePipeConnectionCommand(
            self, self._editor.hydraulicLoops, self._editor.fluids.fluids, self._editor.fluids.WATER
        )

        self.parent.parent().undoStack.push(deleteConnectionCommand)

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
        for s in self.getCorners():
            cornerTupel = (s.pos().x(), s.pos().y())
            corners.append(cornerTupel)

        connectionModel = ConnectionModel(
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
        )

        dictName = "Connection-"
        return dictName, connectionModel.to_dict()

    def decode(self, i):
        model = ConnectionModel.from_dict(i)

        self.id = model.id
        self.connId = model.connectionId
        self.trnsysId = model.trnsysId
        self.setName(model.name)

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)

    def getInternalPiping(self) -> _mfs.InternalPiping:
        fromPort = _mfn.PortItem("Input", _mfn.PortItemType.INPUT)
        toPort = _mfn.PortItem("Output", _mfn.PortItemType.OUTPUT)

        pipe = _mfn.Pipe(self.displayName, self.trnsysId, fromPort, toPort)
        return _mfs.InternalPiping([pipe], {fromPort: self.fromPort, toPort: self.toPort})

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        f = ""
        unitNumber = startingUnit
        typeNr2 = 931  # Temperature calculation from a pipe

        unitText = ""
        ambientT = 20

        loop = self._editor.hydraulicLoops.getLoopForExistingConnection(self)

        densityVar = _hle.getDensityName(loop)
        specHeatVar = _hle.getHeatCapacityName(loop)

        equationConstant1 = 1
        equationConstant2 = 3

        parameterNumber = 6
        inputNumbers = 4

        # Fixed strings
        tempRoomVar = "TRoomStore"
        initialValueS = "20 0.0 20 20"
        powerPrefix = "P"

        # Momentarily hardcoded
        equationNr = 3

        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
        unitText += "!" + self.displayName + "\n"
        unitText += "PARAMETERS " + str(parameterNumber) + "\n"

        diameterInM = self.diameterInCm / 100
        unitText += f"{diameterInM} ! diameter [m]\n"
        unitText += f"{self.lengthInM} ! length [m]\n"
        uValueInkJPerHourM2K = self.uValueInWPerM2K / 1000 * 60 * 60
        unitText += f"{uValueInkJPerHourM2K} ! U-value [kJ/(h*m^2*K)] (= {self.uValueInWPerM2K} W/(m^2*K))\n"
        unitText += densityVar + "\n"
        unitText += specHeatVar + "\n"
        unitText += str(ambientT) + "\n"

        unitText += "INPUTS " + str(inputNumbers) + "\n"

        openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
        assert len(openLoops) == 1
        openLoop = openLoops[0]

        assert len(openLoop.realNodes) == 1
        realNode = openLoop.realNodes[0]

        outputVariables = realNode.serialize(nodesToIndices).outputVariables

        portItemsWithParent = self._getPortItemsWithParent()

        if len(portItemsWithParent) == 2 or True:
            portItem = portItemsWithParent[0][0]
            parent = portItemsWithParent[0][1]
            if hasattr(parent, "getSubBlockOffset"):
                unitText += "T" + parent.displayName + "X" + str(parent.getSubBlockOffset(self) + 1) + "\n"
            else:
                unitText += parent.getTemperatureVariableName(portItem) + "\n"

            unitText += f"{outputVariables[0].name}\n"
            unitText += tempRoomVar + "\n"

            portItem = portItemsWithParent[1][0]
            parent = portItemsWithParent[1][1]
            if hasattr(parent, "getSubBlockOffset"):
                unitText += "T" + parent.displayName + "X" + str(parent.getSubBlockOffset(self) + 1) + "\n"
            else:
                unitText += parent.getTemperatureVariableName(portItem) + "\n"

        else:
            f += (
                "Error: NO VALUE\n" * 3
                + "at connection with parents "
                + str(self.fromPort.parent)
                + str(self.toPort.parent)
                + "\n"
            )

        unitText += "***Initial values\n"
        unitText += initialValueS + "\n\n"

        unitText += "EQUATIONS " + str(equationNr) + "\n"
        unitText += "T" + self.displayName + "= [" + str(unitNumber) + "," + str(equationConstant1) + "]\n"
        unitText += (
            powerPrefix
            + self.displayName
            + "_kW"
            + "= ["
            + str(unitNumber)
            + ","
            + str(equationConstant2)
            + "]/3600 !kW\n"
        )
        unitText += "Mfr" + self.displayName + "= " + "Mfr" + self.displayName + "_A\n\n"

        unitNumber += 1

        return unitText, unitNumber


@_dc.dataclass
class ConnectionModelVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    ConnCID: int
    ConnDisplayName: str
    ConnID: int
    CornerPositions: _tp.List[_tp.Tuple[float, float]]
    FirstSegmentLabelPos: _tp.Tuple[float, float]
    FirstSegmentMassFlowLabelPos: _tp.Tuple[float, float]
    GroupName: str
    PortFromID: int
    PortToID: int
    SegmentPositions: _tp.List[_tp.Tuple[float, float, float, float]]
    trnsysID: int

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("7a15d665-f634-4037-b5af-3662b487a214")


@_dc.dataclass
class ConnectionModel(_ser.UpgradableJsonSchemaMixin):
    DEFAULT_DIAMETER_IN_CM = 2
    DEFAULT_LENGTH_IN_M = 2.0
    DEFAULT_U_VALUE_IN_W_PER_M2_K = 0.8333

    connectionId: int
    name: str
    id: int
    segmentsCorners: _tp.List[_tp.Tuple[float, float]]
    labelPos: _tp.Tuple[float, float]
    massFlowLabelPos: _tp.Tuple[float, float]
    fromPortId: int
    toPortId: int
    trnsysId: int
    diameterInCm: float
    uValueInWPerM2K: float
    lengthInM: float

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,
    ) -> "ConnectionModel":
        data.pop(".__ConnectionDict__")
        connectionModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(ConnectionModel, connectionModel)

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
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return ConnectionModelVersion0

    @classmethod
    def upgrade(cls, superseded: ConnectionModelVersion0) -> "ConnectionModel":
        firstSegmentLabelPos = (
            superseded.SegmentPositions[0][0] + superseded.FirstSegmentLabelPos[0],
            superseded.SegmentPositions[0][1] + superseded.FirstSegmentLabelPos[1],
        )
        firstSegmentMassFlowLabelPos = (
            superseded.SegmentPositions[0][0] + superseded.FirstSegmentMassFlowLabelPos[0],
            superseded.SegmentPositions[0][1] + superseded.FirstSegmentMassFlowLabelPos[1],
        )

        return ConnectionModel(
            superseded.ConnCID,
            superseded.ConnDisplayName,
            superseded.ConnID,
            superseded.CornerPositions,
            firstSegmentLabelPos,
            firstSegmentMassFlowLabelPos,
            superseded.PortFromID,
            superseded.PortToID,
            superseded.trnsysID,
            cls.DEFAULT_DIAMETER_IN_CM,
            cls.DEFAULT_U_VALUE_IN_W_PER_M2_K,
            cls.DEFAULT_LENGTH_IN_M,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("332cd663-684d-414a-b1ec-33fd036f0f17")
