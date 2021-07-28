import dataclasses as _dc
import uuid as _uuid
import typing as _tp
import enum as _enum

import dataclasses_jsonschema as _dcj

import trnsysGUI.serialization as _ser
import trnsysGUI.IdGenerator as _id


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
    HxList: _tp.Sequence["HeatExchangerLegacyVersion"]
    PortPairList: _tp.Sequence["DirectPortPairLegacyVersion"]

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("05f422d3-41fd-48d1-b8d0-4655d9f65247")


@_dc.dataclass
class HeatExchangerLegacyVersion(_dcj.JsonSchemaMixin):
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


@_dc.dataclass
class DirectPortPairLegacyVersion(_dcj.JsonSchemaMixin):
    Side: bool
    Port1offset: float
    Port2offset: float
    Port1ID: int
    Port2ID: int
    ConnID: int
    ConnCID: int
    ConnDisName: str
    trnsysID: int


@_dc.dataclass
class StorageTank(_ser.UpgradableJsonSchemaMixin):
    isHorizontallyFlipped: bool
    isVerticallyFlipped: bool

    BlockName: str
    BlockDisplayName: str

    groupName: str
    id: int
    trnsysId: int

    height: int
    position: _tp.Tuple[float, float]

    heatExchangers: _tp.Sequence["HeatExchanger"]

    directPortPairs: _tp.Sequence["DirectPortPair"]

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,
    ) -> "StorageTank":
        data.pop(".__BlockDict__")
        storageTank = super().from_dict(data, validate, validate_enums)
        return _tp.cast(StorageTank, storageTank)

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
    def upgrade(
        cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0
    ) -> "StorageTank":
        if not isinstance(superseded, StorageTankVersion0):
            raise ValueError(
                f"Can only upgrade a {StorageTankVersion0.__name__} instance."
            )

        heatExchangers = cls._upgradeHeatExchangers(
            superseded.HxList, superseded.size_h
        )
        directPortPairs = cls._upgradeDirectPortPairs(
            superseded.PortPairList, superseded.size_h
        )

        return StorageTank(
            superseded.FlippedH,
            superseded.FlippedV,
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.GroupName,
            superseded.ID,
            superseded.trnsysID,
            superseded.size_h,
            superseded.StoragePosition,
            heatExchangers,
            directPortPairs,
        )

    @classmethod
    def _upgradeHeatExchangers(
        cls,
        supersededHeatExchangers: _tp.Sequence[HeatExchangerLegacyVersion],
        storageTankHeight: float,
    ) -> _tp.Sequence["HeatExchanger"]:
        heatExchangers = []
        for supersededHeatExchanger in supersededHeatExchangers:
            heatExchangerLegacyVersion = HeatExchangerVersion0.createFromLegacyHeatExchanger(
                supersededHeatExchanger, storageTankHeight
            )

            heatExchanger = HeatExchanger.fromInstance(heatExchangerLegacyVersion)

            heatExchangers.append(heatExchanger)

        return heatExchangers

    @classmethod
    def _upgradeDirectPortPairs(
        cls,
        supersededPairs: _tp.Sequence[DirectPortPairLegacyVersion],
        storageTankHeight: float,
    ) -> _tp.Sequence["DirectPortPair"]:
        directPortPairs = []
        for supersededPair in supersededPairs:
            directPortPairLegacyVersion = DirectPortPairVersion0.createFromLegacyPortPair(
                    supersededPair, storageTankHeight
            )

            directPortPair = DirectPortPair.fromInstance(directPortPairLegacyVersion)

            directPortPairs.append(directPortPair)

        return directPortPairs

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("05f422d3-41fd-48d1-b8d0-4655d9f65247")

    @classmethod
    def getSupersededClass(cls):
        return StorageTankVersion0


class Side(_enum.Enum):
    LEFT = "left"
    RIGHT = "right"

    @staticmethod
    def createFromSideNr(sideNr: int) -> "Side":
        if sideNr == 2:
            return Side.RIGHT

        if sideNr == 0:
            return Side.LEFT

        raise ValueError(f"Unknown side number: {sideNr}")

    def toSideNr(self):
        if self == self.LEFT:
            return 0

        if self == self.RIGHT:
            return 2

        raise ValueError("Cannot convert {self} to side nr.")


@_dc.dataclass
class Port(_dcj.JsonSchemaMixin):
    id: int
    relativeHeight: float


@_dc.dataclass
class PortPairVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    side: Side

    name: str

    inputPort: Port
    outputPort: Port

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('e1b81a7b-51ca-44f0-9d3a-6b6c42eb8e91')


@_dc.dataclass
class PortPair(_ser.UpgradableJsonSchemaMixin):
    side: Side

    trnsysId: int
    inputPort: Port
    outputPort: Port

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return PortPairVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "PortPair":
        if not isinstance(superseded, PortPairVersion0):
            raise ValueError(
                f"Superseded instance is not of type {PortPairVersion0.__name__}"
            )

        return PortPair(
            superseded.side,
            _id.IdGenerator.UNINITIALIZED_ID,  # type: ignore[attr-defined]
            superseded.inputPort,
            superseded.outputPort
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('ed17e7a7-4798-4a80-beb7-81730523cf35')


@_dc.dataclass
class HeatExchangerVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    portPair: PortPairVersion0

    width: float

    parentId: int

    id: int
    connectionTrnsysId: int

    @classmethod
    def createFromLegacyHeatExchanger(
        cls,
        superseded: HeatExchangerLegacyVersion,
        storageTankHeight: float,
    ) -> "HeatExchangerVersion0":
        absoluteInputHeight = storageTankHeight - superseded.Offset[1]
        absoluteOutputHeight = absoluteInputHeight - superseded.Height

        relativeInputHeight = round(absoluteInputHeight / storageTankHeight, 2)
        relativeOutputHeight = round(absoluteOutputHeight / storageTankHeight, 2)

        inputPort = Port(superseded.Port1ID, relativeInputHeight)
        outputPort = Port(superseded.Port2ID, relativeOutputHeight)

        side = Side.createFromSideNr(superseded.SideNr)

        portPair = PortPairVersion0(side, superseded.DisplayName, inputPort, outputPort)

        heatExchanger = HeatExchangerVersion0(
            portPair,
            superseded.Width,
            superseded.ParentID,
            superseded.ID,
            superseded.connTrnsysID,
        )

        return heatExchanger

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("23938d79-dc02-4752-ba1b-25d7a610de27")


@_dc.dataclass
class HeatExchangerVersion1(_ser.UpgradableJsonSchemaMixin):
    portPair: PortPairVersion0
    width: float
    parentId: int
    id: int

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return HeatExchangerVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "HeatExchangerVersion1":
        if not isinstance(superseded, HeatExchangerVersion0):
            raise ValueError(
                f"`superseded` is not of type {HeatExchangerVersion0.__name__}"
            )

        return HeatExchangerVersion1(
            superseded.portPair, superseded.width, superseded.parentId, superseded.id
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("68c5cebb-0c47-4dec-8c85-8872b7f6c238")


@_dc.dataclass
class HeatExchanger(_ser.UpgradableJsonSchemaMixin):
    portPair: PortPair
    name: str
    width: float
    parentId: int
    id: int

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return HeatExchangerVersion1

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "HeatExchanger":
        if not isinstance(superseded, HeatExchangerVersion1):
            raise ValueError(
                f"`superseded` is not of type {HeatExchangerVersion1.__name__}"
            )

        portPair = PortPair.fromInstance(superseded.portPair)

        return HeatExchanger(
            portPair, superseded.portPair.name, superseded.width, superseded.parentId, superseded.id
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('be068f84-2627-4f53-87a9-9a1f4fd1c529')


@_dc.dataclass
class DirectPortPairVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    portPair: PortPairVersion0

    id: int

    connectionId: int
    trnsysId: int

    @classmethod
    def createFromLegacyPortPair(
        cls, superseded: DirectPortPairLegacyVersion, storageTankHeight: float
    ) -> "DirectPortPairVersion0":
        absoluteInputHeight = storageTankHeight - superseded.Port1offset
        relativeInputHeight = round(absoluteInputHeight / storageTankHeight, 2)
        inputPort = Port(superseded.Port1ID, relativeInputHeight)

        absoluteOutputHeight = storageTankHeight - superseded.Port2offset
        relativeOutputHeight = round(absoluteOutputHeight / storageTankHeight, 2)
        outputPort = Port(superseded.Port2ID, relativeOutputHeight)

        side = Side.LEFT if superseded.Side else Side.RIGHT
        portPair = PortPairVersion0(side, superseded.ConnDisName, inputPort, outputPort)

        return DirectPortPairVersion0(
            portPair,
            superseded.ConnID,
            superseded.ConnCID,
            superseded.trnsysID,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("2629b768-3cfe-4bff-b28d-658ab6154202")


@_dc.dataclass
class DirectPortPair(_ser.UpgradableJsonSchemaMixin):
    portPair: PortPair

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return DirectPortPairVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "DirectPortPair":
        if not isinstance(superseded, DirectPortPairVersion0):
            raise ValueError(
                f"Superseded instance is not of type {DirectPortPairVersion0.__name__}"
            )

        portPair = PortPair.fromInstance(superseded.portPair)

        return DirectPortPair(portPair)

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("67aaee05-7d09-40e1-a6e2-d367c7196832")
