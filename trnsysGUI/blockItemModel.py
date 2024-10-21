import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.serialization as _gser


@_dc.dataclass
class BlockItemModelVersion0(
    _ser.UpgradableJsonSchemaMixinVersion0, _gser.RequiredDecoderFieldsMixin
):  # pylint: disable=too-many-instance-attributes
    BlockPosition: _tp.Tuple[float, float]  # pylint: disable=invalid-name
    ID: int  # pylint: disable=invalid-name
    trnsysID: int
    PortsIDIn: _tp.List[int]  # pylint: disable=invalid-name
    PortsIDOut: _tp.List[int]  # pylint: disable=invalid-name
    FlippedH: bool  # pylint: disable=invalid-name
    FlippedV: bool  # pylint: disable=invalid-name
    RotationN: int  # pylint: disable=invalid-name
    GroupName: str  # pylint: disable=invalid-name

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("b87a3360-eaa7-48f3-9bed-d01224727cbe")


@_dc.dataclass
class BlockItemModelVersion1(
    _ser.UpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin
):  # pylint: disable=too-many-instance-attributes
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable=invalid-name
    trnsysId: int
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return BlockItemModelVersion0

    @classmethod
    def upgrade(cls, superseded: BlockItemModelVersion0) -> "BlockItemModelVersion1":  # type: ignore[override]

        return BlockItemModelVersion1(
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.BlockPosition,
            superseded.ID,
            superseded.trnsysID,
            superseded.PortsIDIn,
            superseded.PortsIDOut,
            superseded.FlippedH,
            superseded.FlippedV,
            superseded.RotationN,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("bbc03f36-d1a1-4d97-a9c0-d212ea3a0203")


@_dc.dataclass
class BlockItemModel(
    _gser.BlockItemUpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin
):  # pylint: disable=too-many-instance-attributes
    blockPosition: _tp.Tuple[float, float]
    trnsysId: int
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,  # pylint: disable=duplicate-code
        validate=True,
        validate_enums: bool = True,
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> "BlockItemModel":
        blockItemModel = super().from_dict(data, validate, validate_enums, schema_type)
        return _tp.cast(BlockItemModel, blockItemModel)

    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return BlockItemModelVersion1

    @classmethod
    def upgrade(cls, superseded: BlockItemModelVersion1) -> "BlockItemModel":  # type: ignore[override]

        return BlockItemModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.blockPosition,
            superseded.trnsysId,
            superseded.portsIdsIn,
            superseded.portsIdsOut,
            superseded.flippedH,
            superseded.flippedV,
            superseded.rotationN,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("e8cfde2f-8239-4338-a5f0-63a7abb93900")


@_dc.dataclass
class BlockItemBaseModelVersion0(
    _ser.UpgradableJsonSchemaMixinVersion0
):  # pylint: disable=too-many-instance-attributes
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable=invalid-name,duplicate-code # 1
    trnsysId: int
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("4f64dfcd-a0cf-45fd-a788-ff774c5b608f")


@_dc.dataclass
class BlockItemBaseModel(_ser.UpgradableJsonSchemaMixin):
    blockPosition: _tp.Tuple[float, float]
    trnsysId: int
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return BlockItemBaseModelVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "BlockItemBaseModel":
        assert isinstance(superseded, BlockItemBaseModelVersion0)

        blockItemModel = createBlockItemBaseModelFromLegacyModel(superseded)

        return blockItemModel

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("7b792574-5fa6-4c3e-b2e3-7e4eb71d7746")


class BlockItemLegacyModelProtocol(_tp.Protocol):
    blockPosition: _tp.Tuple[float, float]
    trnsysId: int
    flippedH: bool
    flippedV: bool
    rotationN: int


def createBlockItemBaseModelFromLegacyModel(superseded: BlockItemLegacyModelProtocol) -> BlockItemBaseModel:
    return BlockItemBaseModel(
        superseded.blockPosition, superseded.trnsysId, superseded.flippedH, superseded.flippedV, superseded.rotationN
    )
