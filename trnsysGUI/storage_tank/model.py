import dataclasses as _dc
import uuid as _uuid
import typing as _tp
import enum as _enum

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
    PortPairList: _tp.Sequence["DirectPortPairVersion0"]

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("05f422d3-41fd-48d1-b8d0-4655d9f65247")


@_dc.dataclass
class HeatExchangerVersion0(_dcj.JsonSchemaMixin):
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
class DirectPortPairVersion0(_dcj.JsonSchemaMixin):
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
        validate_enums: bool = True,
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def upgrade(cls, superseded: StorageTankVersion0) -> "StorageTank":
        heatExchangers = cls._upgradeHeatExchangers(
            superseded.HxList,
            superseded.size_h
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
        supersededHeatExchangers: _tp.Sequence[HeatExchangerVersion0],
        storageTankHeight: float,
    ) -> _tp.Sequence["HeatExchanger"]:
        heatExchangers = []
        for supersededHeatExchanger in supersededHeatExchangers:
            heatExchanger = HeatExchanger.createFromSupersededHeatExchanger(
                supersededHeatExchanger, storageTankHeight
            )
            heatExchangers.append(heatExchanger)

        return heatExchangers

    @classmethod
    def _upgradeDirectPortPairs(
        cls,
        supersededPairs: _tp.Sequence[DirectPortPairVersion0],
        storageTankHeight: float,
    ) -> _tp.Sequence["DirectPortPair"]:
        directPortPairs = []
        for supersededPair in supersededPairs:
            directPortPair = DirectPortPair.createFromSupersededPortPair(
                supersededPair, storageTankHeight
            )
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
class PortPair(_dcj.JsonSchemaMixin):
    side: Side
    name: str
    inputPort: Port
    outputPort: Port


@_dc.dataclass
class HeatExchanger(_dcj.JsonSchemaMixin):
    portPair: PortPair

    width: float

    parentId: int
    id: int
    connectionTrnsysId: int

    @classmethod
    def createFromSupersededHeatExchanger(
        cls,
        superseded: HeatExchangerVersion0,
        storageTankHeight: float,
    ) -> "HeatExchanger":
        absoluteInputHeight = storageTankHeight - superseded.Offset[1]
        absoluteOutputHeight = absoluteInputHeight - superseded.Height

        relativeInputHeight = round(absoluteInputHeight / storageTankHeight, 2)
        relativeOutputHeight = round(absoluteOutputHeight / storageTankHeight, 2)

        inputPort = Port(superseded.Port1ID, relativeInputHeight)
        outputPort = Port(superseded.Port2ID, relativeOutputHeight)

        side = Side.createFromSideNr(superseded.SideNr)

        portPair = PortPair(side, superseded.DisplayName, inputPort, outputPort)

        return HeatExchanger(
            portPair,
            superseded.Width,
            superseded.ParentID,
            superseded.ID,
            superseded.connTrnsysID,
        )


@_dc.dataclass
class DirectPortPair(_dcj.JsonSchemaMixin):
    portPair: PortPair

    id: int
    connectionId: int
    trnsysId: int

    @classmethod
    def createFromSupersededPortPair(
        cls, superseded: DirectPortPairVersion0, storageTankHeight: float
    ) -> "DirectPortPair":
        absoluteInputHeight = storageTankHeight - superseded.Port1offset
        relativeInputHeight = round(absoluteInputHeight / storageTankHeight, 2)
        inputPort = Port(superseded.Port1ID, relativeInputHeight)

        absoluteOutputHeight = storageTankHeight - superseded.Port2offset
        relativeOutputHeight = round(absoluteOutputHeight / storageTankHeight, 2)
        outputPort = Port(superseded.Port2ID, relativeOutputHeight)

        side = Side.LEFT if superseded.Side else Side.RIGHT
        portPair = PortPair(side, superseded.ConnDisName, inputPort, outputPort)

        return DirectPortPair(
            portPair,
            superseded.ConnID,
            superseded.ConnCID,
            superseded.trnsysID,
        )
