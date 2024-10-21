import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser

import trnsysGUI.serialization as _gser

import trnsysGUI.connection.doublePipeDefaultValues as _defaults


@_dc.dataclass
class DoublePipeConnectionModelVersion0(  # pylint: disable=too-many-instance-attributes
    _ser.UpgradableJsonSchemaMixinVersion0
):
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
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("0810c9ea-85df-4431-bb40-3190c25c9161")


@_dc.dataclass
class DoublePipeConnectionModelVersion1(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
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
    lengthInM: float

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return DoublePipeConnectionModelVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "DoublePipeConnectionModelVersion1":
        assert isinstance(superseded, DoublePipeConnectionModelVersion0)

        return DoublePipeConnectionModelVersion1(
            superseded.connectionId,
            superseded.name,
            superseded.id,
            superseded.childIds,
            superseded.segmentsCorners,
            superseded.labelPos,
            superseded.massFlowLabelPos,
            superseded.fromPortId,
            superseded.toPortId,
            superseded.trnsysId,
            _defaults.DEFAULT_DOUBLE_PIPE_LENGTH_IN_M,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("bdb5f03b-75bb-4c2f-a658-0de489c5b017")


@_dc.dataclass
class DoublePipeConnectionModel(
    _gser.ConnectionItemUpgradableJsonSchemaMixin
):  # pylint: disable=too-many-instance-attributes
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
    lengthInM: float
    shallBeSimulated: bool

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return DoublePipeConnectionModelVersion1

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "DoublePipeConnectionModel":
        assert isinstance(superseded, DoublePipeConnectionModelVersion1)

        return DoublePipeConnectionModel(
            superseded.connectionId,
            superseded.name,
            superseded.id,
            superseded.childIds,
            superseded.segmentsCorners,
            superseded.labelPos,
            superseded.massFlowLabelPos,
            superseded.fromPortId,
            superseded.toPortId,
            superseded.trnsysId,
            superseded.lengthInM,
            _defaults.DEFAULT_SHALL_BE_SIMULATED,
        )

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,  # pylint: disable=duplicate-code  # 1
        validate=True,
        validate_enums: bool = True,  # /NOSONAR
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> "DoublePipeConnectionModel":
        doublePipeConnectionModel = super().from_dict(data, validate, validate_enums, schema_type)
        return _tp.cast(DoublePipeConnectionModel, doublePipeConnectionModel)

    def to_dict(
        self,
        omit_none: bool = True,  # /NOSONAR
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code # 1 # /NOSONAR
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums, schema_type)
        return data

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("62a1383d-5a0b-4886-9951-31ffd732637d")
