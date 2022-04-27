import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser

import trnsysGUI.connection.values as _values


@_dc.dataclass
class ConnectionModelVersion0(_ser.UpgradableJsonSchemaMixinVersion0):  # pylint: disable=too-many-instance-attributes
    ConnCID: int  # pylint: disable=invalid-name
    ConnDisplayName: str  # pylint: disable=invalid-name
    ConnID: int  # pylint: disable=invalid-name
    CornerPositions: _tp.List[_tp.Tuple[float, float]]  # pylint: disable=invalid-name
    FirstSegmentLabelPos: _tp.Tuple[float, float]  # pylint: disable=invalid-name
    FirstSegmentMassFlowLabelPos: _tp.Optional[_tp.Tuple[float, float]]  # pylint: disable=invalid-name
    GroupName: str  # pylint: disable=invalid-name
    PortFromID: int  # pylint: disable=invalid-name
    PortToID: int  # pylint: disable=invalid-name
    SegmentPositions: _tp.List[_tp.Tuple[float, float, float, float]]  # pylint: disable=invalid-name
    isVirtualConn: _tp.Optional[bool]
    trnsysID: int

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("7a15d665-f634-4037-b5af-3662b487a214")


@_dc.dataclass
class ConnectionModelVersion1(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    connectionId: int
    name: str
    groupName: _tp.Optional[str]
    id: int  # pylint: disable=invalid-name
    segmentsCorners: _tp.List[_tp.Tuple[float, float]]
    labelPos: _tp.Tuple[float, float]
    massFlowLabelPos: _tp.Tuple[float, float]
    fromPortId: int
    toPortId: int
    trnsysId: int
    diameterInCm: _values.Value = _values.DEFAULT_DIAMETER_IN_CM
    uValueInWPerM2K: _values.Value = _values.DEFAULT_U_VALUE_IN_W_PER_M2_K
    lengthInM: _values.Value = _values.DEFAULT_LENGTH_IN_M

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

        if superseded.FirstSegmentMassFlowLabelPos:
            firstSegmentMassFlowLabelPos = (
                superseded.SegmentPositions[0][0] + superseded.FirstSegmentMassFlowLabelPos[0],
                superseded.SegmentPositions[0][1] + superseded.FirstSegmentMassFlowLabelPos[1],
            )
        else:
            firstSegmentMassFlowLabelPos = firstSegmentLabelPos

        return ConnectionModelVersion1(
            superseded.ConnCID,
            superseded.ConnDisplayName,
            None,
            superseded.ConnID,
            superseded.CornerPositions,
            firstSegmentLabelPos,
            firstSegmentMassFlowLabelPos,
            superseded.PortFromID,
            superseded.PortToID,
            superseded.trnsysID,
            _values.DEFAULT_DIAMETER_IN_CM,
            _values.DEFAULT_U_VALUE_IN_W_PER_M2_K,
            _values.DEFAULT_LENGTH_IN_M,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("332cd663-684d-414a-b1ec-33fd036f0f17")


@_dc.dataclass
class ConnectionModel(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    connectionId: int
    name: str
    id: int  # pylint: disable=invalid-name
    segmentsCorners: _tp.List[_tp.Tuple[float, float]]
    labelPos: _tp.Tuple[float, float]
    massFlowLabelPos: _tp.Tuple[float, float]
    fromPortId: int
    toPortId: int
    trnsysId: int
    diameterInCm: _values.Value
    uValueInWPerM2K: _values.Value
    lengthInM: _values.Value

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
        return ConnectionModelVersion1

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "ConnectionModel":
        assert isinstance(superseded, ConnectionModelVersion1)

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
            superseded.diameterInCm,
            superseded.uValueInWPerM2K,
            superseded.lengthInM,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("f03faf46-4d0e-4407-a604-90925d83d43a")
