import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import pytrnsys.utils.serialization as _ser


@_dc.dataclass
class Variable(_ser.UpgradableJsonSchemaMixinVersion0):
    name: str

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('3196024b-6775-42bc-92d2-e11d60c64bac')


@_dc.dataclass(frozen=True, eq=False)
class Fluid(_ser.UpgradableJsonSchemaMixinVersion0):
    name: str
    specificHeatCapacityInJPerKgK: _tp.Union[float, Variable]
    densityInKgPerM3: _tp.Union[float, Variable]

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
