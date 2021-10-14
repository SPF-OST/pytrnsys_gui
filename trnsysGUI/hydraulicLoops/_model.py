from __future__ import annotations

__all__ = ["Connection", "Fluid", "HydraulicLoop"]

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import trnsysGUI.serialization as _ser

if _tp.TYPE_CHECKING:
    import trnsysGUI.Connection as _conn


@_dc.dataclass
class Connection:
    name: str
    diameterInCm: float
    uValueInWPerM2K: float
    connection: _conn.Connection  # type: ignore[name-defined]


@_dc.dataclass
class Fluid(_ser.UpgradableJsonSchemaMixinVersion0):
    name: str
    specificHeatCapacityInJPerKgK: float
    densityInKgPerM3: float

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('5b1d8eb8-e9c0-4c6a-b14f-0a7216b60132')


class PredefinedFluids:
    # If you add fluids here, don't forget to add them to `getAllFluids` below!
    WATER = Fluid("water", specificHeatCapacityInJPerKgK=418.45, densityInKgPerM3=997)
    BRINE = Fluid("brine", specificHeatCapacityInJPerKgK=2360, densityInKgPerM3=1113.2)

    @classmethod
    def getAllFluids(cls) -> _tp.Sequence[Fluid]:
        return [
            cls.WATER,
            cls.BRINE
        ]


@_dc.dataclass
class HydraulicLoop:
    name: str
    fluid: Fluid
    connections: _tp.Sequence[Connection]
