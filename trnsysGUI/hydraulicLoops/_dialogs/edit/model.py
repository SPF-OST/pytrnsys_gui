from __future__ import annotations

__all__ = ["Connection", "HydraulicLoop"]

import dataclasses as _dc
import typing as _tp
import collections.abc as _cabc

import trnsysGUI.hydraulicLoops.connectionsDefinitionMode as _cdm
from trnsysGUI.hydraulicLoops import _serialization as _ser

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc


@_dc.dataclass
class Connection:
    name: str
    diameterInCm: float
    uValueInWPerM2K: float
    lengthInM: float
    shallBeSimulated: bool
    connection: _spc.SinglePipeConnection


@_dc.dataclass
class HydraulicLoop:
    name: str
    fluid: _ser.Fluid
    connectionsDefinitionMode: _cdm.ConnectionsDefinitionMode
    connections: _cabc.Sequence[Connection]

    @property
    def nConnections(self) -> int:
        return len(self.connections)

    @property
    def simulatedConnections(self) -> _cabc.Sequence[Connection]:
        return [c for c in self.connections if c.shallBeSimulated]

    @property
    def nSimulatedConnections(self) -> int:
        return len(self.simulatedConnections)
