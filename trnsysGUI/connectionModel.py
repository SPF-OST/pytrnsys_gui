import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

from trnsysGUI import serialization as _ser


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
class ConnectionModelVersion1(_ser.UpgradableJsonSchemaMixin):

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
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return ConnectionModelVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "ConnectionModelVersion1":
        assert isinstance(superseded, ConnectionModelVersion0)

        firstSegmentLabelPos = (
            superseded.SegmentPositions[0][0] + superseded.FirstSegmentLabelPos[0],
            superseded.SegmentPositions[0][1] + superseded.FirstSegmentLabelPos[1],
        )
        firstSegmentMassFlowLabelPos = (
            superseded.SegmentPositions[0][0] + superseded.FirstSegmentMassFlowLabelPos[0],
            superseded.SegmentPositions[0][1] + superseded.FirstSegmentMassFlowLabelPos[1],
        )

        return ConnectionModelVersion1(
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
        return _uuid.UUID("332cd663-684d-414a-b1ec-33fd036f0f17")


@_dc.dataclass
class ConnectionModelVersion2(_ser.UpgradableJsonSchemaMixin):
    DEFAULT_DIAMETER_IN_CM = 2
    DEFAULT_LENGTH_IN_M = 2.0
    DEFAULT_U_VALUE_IN_W_PER_M2_K = 320

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
    diameterInCm: float
    uValueInWPerM2K: float
    lengthInM: float

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return ConnectionModelVersion1

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "ConnectionModelVersion2":
        assert isinstance(superseded, ConnectionModelVersion1)

        return ConnectionModelVersion2(
            superseded.connectionId,
            superseded.name,
            superseded.id,
            superseded.segmentsCorners,
            superseded.labelPos,
            superseded.massFlowLabelPos,
            superseded.groupName,
            superseded.fromPortId,
            superseded.toPortId,
            superseded.trnsysId,
            cls.DEFAULT_DIAMETER_IN_CM,
            cls.DEFAULT_U_VALUE_IN_W_PER_M2_K,
            cls.DEFAULT_LENGTH_IN_M,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("1a1c2140-d710-4fae-983e-90dcecc609ec")


@_dc.dataclass
class ConnectionModel(_ser.UpgradableJsonSchemaMixin):
    DEFAULT_DIAMETER_IN_CM = 2
    DEFAULT_LENGTH_IN_M = 2.0
    DEFAULT_U_VALUE_IN_W_PER_M2_K = 320

    @classmethod
    def from_dict(  # pylint: disable=duplicate-code  # 2
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
        validate_enums: bool = True,  # pylint: disable=duplicate-code  # 3
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__ConnectionDict__"] = True
        return data

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
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return ConnectionModelVersion2

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "ConnectionModel":
        assert isinstance(superseded, ConnectionModelVersion2)

        return ConnectionModel(
            superseded.connectionId,
            superseded.name,
            superseded.id,
            superseded.segmentsCorners,
            superseded.labelPos,
            superseded.massFlowLabelPos,
            superseded.fromPortId,
            superseded.toPortId,
            superseded.trnsysId,
            cls.DEFAULT_DIAMETER_IN_CM,
            cls.DEFAULT_U_VALUE_IN_W_PER_M2_K,
            cls.DEFAULT_LENGTH_IN_M,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('0282bd53-3157-4266-9641-19df2f54d167')
