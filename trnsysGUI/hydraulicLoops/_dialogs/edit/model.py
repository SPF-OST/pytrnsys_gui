from __future__ import annotations

__all__ = ["Connection", "HydraulicLoop"]

import dataclasses as _dc
import typing as _tp

from trnsysGUI.hydraulicLoops import _serialization as _ser

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc


@_dc.dataclass
class Connection:
    name: str
    diameterInCm: float
    uValueInWPerM2K: float
    lengthInM: float
    connection: _spc.SinglePipeConnection


@_dc.dataclass
class HydraulicLoop:
    name: str
    fluid: _ser.Fluid
    useLoopWideDefaults: bool
    connections: _tp.Sequence[Connection]
