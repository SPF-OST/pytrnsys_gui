# pylint: skip-file
# type: ignore

from __future__ import annotations

import dataclasses as _dc
import math as _math
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.serialization as _ser
from massFlowSolver import InternalPiping
from trnsysGUI.Connection import Connection
from trnsysGUI.PortItemBase import PortItemBase
from trnsysGUI.connection.segmentItemFactory import SegmentItemFactoryBase

if _tp.TYPE_CHECKING:
    pass


def calcDist(p1, p2):
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class SinglePipeConnection(Connection):
    def __init__(self, fromPort: PortItemBase, toPort: PortItemBase, segmentItemFactory: SegmentItemFactoryBase, parent):
        super().__init__(fromPort, toPort, segmentItemFactory, parent)

    # Saving / Loading
    def encode(self):
        self.logger.debug("Encoding a connection")

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
            self.groupName,
            self.fromPort.id,
            self.toPort.id,
            self.trnsysId,
        )

        dictName = "Connection-"
        return dictName, connectionModel.to_dict()

    def decode(self, i):
        self.logger.debug("Loading a connection in Decoder")

        model = ConnectionModel.from_dict(i)

        self.id = model.id
        self.connId = model.connectionId
        self.trnsysId = model.trnsysId
        self.setName(model.name)
        self.groupName = "defaultGroup"
        self.setConnToGroup(model.groupName)

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)

    def getInternalPiping(self) -> InternalPiping:
        fromPort = _mfn.PortItem()
        toPort = _mfn.PortItem()

        pipe = _mfn.Pipe(self.displayName, self.trnsysId, fromPort, toPort)
        return InternalPiping([pipe], {fromPort: self.fromPort, toPort: self.toPort})

    def _getConnectedRealNode(self, portItem: _mfn.PortItem, internalPiping: _mfs.InternalPiping) -> _tp.Optional[_mfn.RealNodeBase]:
        assert portItem in internalPiping.modelPortItemsToGraphicalPortItem, "`portItem' doesn't belong to `internalPiping'"

        graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]

        assert graphicalPortItem in [self.fromPort, self.toPort],\
            "This connection is not connected to `graphicalPortItem'"

        blockItem: _mfs.MassFlowNetworkContributorMixin = graphicalPortItem.parent
        blockItemInternalPiping = blockItem.getInternalPiping()

        for startingNode in blockItemInternalPiping.openLoopsStartingNodes:
            realNodesAndPortItems = _mfn.getConnectedRealNodesAndPortItems(startingNode)
            for realNode in realNodesAndPortItems.realNodes:
                for portItem in [n for n in realNode.getNeighbours() if isinstance(n, _mfn.PortItem)]:
                    candidateGraphicalPortItem = blockItemInternalPiping.modelPortItemsToGraphicalPortItem[portItem]
                    if candidateGraphicalPortItem == graphicalPortItem:
                        return realNode
        return None


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
        return _uuid.UUID('7a15d665-f634-4037-b5af-3662b487a214')


@_dc.dataclass
class ConnectionModel(_ser.UpgradableJsonSchemaMixin):
    connectionId: int
    name: str
    id: int
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
        firstSegmentLabelPos = superseded.SegmentPositions[0][0] + superseded.FirstSegmentLabelPos[0], \
                               superseded.SegmentPositions[0][1] + superseded.FirstSegmentLabelPos[1]
        firstSegmentMassFlowLabelPos = superseded.SegmentPositions[0][0] + superseded.FirstSegmentMassFlowLabelPos[0], \
                                       superseded.SegmentPositions[0][1] + superseded.FirstSegmentMassFlowLabelPos[1]

        return ConnectionModel(
            superseded.ConnCID,
            superseded.ConnDisplayName,
            superseded.ConnID,
            superseded.CornerPositions,
            firstSegmentLabelPos,
            firstSegmentMassFlowLabelPos,
            superseded.GroupName,
            superseded.PortFromID,
            superseded.PortToID,
            superseded.trnsysID,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('332cd663-684d-414a-b1ec-33fd036f0f17')