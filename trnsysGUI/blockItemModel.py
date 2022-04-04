import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser


@_dc.dataclass
class BlockItemModelVersion0(_ser.UpgradableJsonSchemaMixinVersion0):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable=invalid-name
    BlockDisplayName: str  # pylint: disable=invalid-name
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
class BlockItemModel(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable=invalid-name
    BlockDisplayName: str  # pylint: disable=invalid-name
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable=invalid-name
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
    ) -> "BlockItemModel":
        del data[".__BlockDict__"]
        blockItemModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(BlockItemModel, blockItemModel)

    def to_dict(
            self,
            omit_none: bool = True,
            validate: bool = False,
            validate_enums: bool = True,  # pylint: disable=duplicate-code
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return BlockItemModelVersion0

    @classmethod
    def upgrade(cls, superseded: BlockItemModelVersion0) -> "BlockItemModel":  # type: ignore[override]

        return BlockItemModel(
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
