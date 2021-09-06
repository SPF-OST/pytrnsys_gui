from __future__ import annotations

__all__ = ["Connection", "Fluid", "HydraulicLoop"]

import dataclasses as _dc
import typing as _tp

if _tp.TYPE_CHECKING:
    import trnsysGUI.Connection as _conn


@_dc.dataclass
class Connection:
    name: str
    diameterInCm: float
    connection: _conn.Connection  # type: ignore[name-defined]


@_dc.dataclass
class Fluid:
    name: str
    specificHeatCapacityInJPerKgK: float


@_dc.dataclass
class HydraulicLoop:
    name: str
    fluid: Fluid
    connections: _tp.Sequence[Connection]
