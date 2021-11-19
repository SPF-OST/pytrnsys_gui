from __future__ import annotations

__all__ = ["Connection", "HydraulicLoop"]

import dataclasses as _dc
import typing as _tp

from .. import _serialization as _ser

if _tp.TYPE_CHECKING:
    import trnsysGUI.Connection as _conn


@_dc.dataclass
class Connection:
    name: str
    diameterInCm: float
    uValueInWPerM2K: float
    lengthInM: float
    connection: _conn.Connection  # type: ignore[name-defined]


@_dc.dataclass
class HydraulicLoop:
    name: str
    fluid: _ser.Fluid
    connections: _tp.Sequence[Connection]
