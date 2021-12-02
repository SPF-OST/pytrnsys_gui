import dataclasses as _dc
import typing as _tp
import uuid as _uuid

from trnsysGUI import serialization as _ser


@_dc.dataclass(frozen=True, eq=False)
class Fluid(_ser.UpgradableJsonSchemaMixinVersion0):
    name: str
    specificHeatCapacityInJPerKgK: float
    densityInKgPerM3: float

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('5b1d8eb8-e9c0-4c6a-b14f-0a7216b60132')


@_dc.dataclass
class HydraulicLoop(_ser.UpgradableJsonSchemaMixinVersion0):
    name: str
    hasUserDefinedName: bool
    fluidName: str
    connectionsTrnsysId: _tp.Sequence[int]

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('0047cab1-dd67-42ee-af45-5e5d30d97a92')
