import dataclasses as _dc
import uuid as _uuid
import typing as _tp

import dataclasses_jsonschema as _dcj

import trnsysGUI.serialization as _ser


@_dc.dataclass
class StorageTankVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    FlippedH: bool
    FlippedV: bool
    BlockName: str
    BlockDisplayName: str
    size_h: int
    StoragePosition: _tp.Tuple[float, float]
    trnsysID: int
    ID: int
    GroupName: str
    HxList: _tp.Sequence["HeatExchangerVersion0"]
    PortPairList: _tp.Sequence["PortPairVersion0"]

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,
    ) -> "StorageTankVersion0":
        data = data.copy()
        data.pop(".__BlockDict__")

        result = super().from_dict(data, validate, validate_enums)

        return _tp.cast(cls, result)

    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,
    ) -> _dcj.JsonDict:
        data = super().to_dict()
        data[".__BlockDict__"] = True

        return data

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('05f422d3-41fd-48d1-b8d0-4655d9f65247')


@_dc.dataclass
class HeatExchangerVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    SideNr: int
    Width: float
    Height: float
    Offset: _tp.Tuple[float, float]
    DisplayName: str
    ParentID: int
    Port1ID: int
    Port2ID: int
    connTrnsysID: int
    ID: int

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('8ba7817b-2cf2-471a-8241-636c38a758e9')


@_dc.dataclass
class PortPairVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    Side: bool
    Port1offset: float
    Port2offset: float
    Port1ID: int
    Port2ID: int
    ConnID: int
    ConnCID: int
    ConnDisName: str
    trnsysID: int

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('425a4516-4d39-4f1f-a31c-920a2b9f823e')
