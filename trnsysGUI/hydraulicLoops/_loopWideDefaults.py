from __future__ import annotations

__all__ = ["resetConnectionPropertiesToLoopWideDefaults"]

import typing as _tp

import trnsysGUI.connection.values as _values

from . import names as _names


if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc


def resetConnectionPropertiesToLoopWideDefaults(
    connections: _tp.Sequence[_spc.SinglePipeConnection], loopName: str  # type: ignore[name-defined]
) -> None:
    for connection in connections:
        connection.lengthInM = _values.Variable(_names.getDefaultLengthName(loopName))
        connection.diameterInCm = _values.Variable(_names.getDefaultDiameterName(loopName))
        connection.uValueInWPerM2K = _values.Variable(_names.getDefaultUValueName(loopName))
