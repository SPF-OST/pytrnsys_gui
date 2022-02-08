import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

from trnsysGUI import serialization as _ser


@_dc.dataclass
class BlockItemModelVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    BlockName: str
    BlockDisplayName: str
    BlockPosition: _tp.Tuple[float, float]
    ID: int
    trnsysID: int
    PortsIDIn: _tp.List[int]
    PortsIDOut: _tp.List[int]
    FlippedH: bool
    FlippedV: bool
    RotationN: int
    GroupName: str

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("b87a3360-eaa7-48f3-9bed-d01224727cbe")


@_dc.dataclass
class BlockItemModel(_ser.UpgradableJsonSchemaMixin):
    BlockName: str
    BlockDisplayName: str
    blockPosition: _tp.Tuple[float, float]
    Id: int
    trnsysId: int
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,
    ) -> "BlockItemModel":
        data.pop(".__BlockDict__")
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
    def upgrade(cls, superseded: BlockItemModelVersion0) -> "BlockItemModel":

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