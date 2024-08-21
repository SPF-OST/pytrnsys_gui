from __future__ import annotations

import typing as _tp

import trnsysGUI.connection.values as _values
from . import connectionsDefinitionMode as _cdm
from . import names as _names

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc


def setConnectionPropertiesForDefinitionMode(
    connections: _tp.Sequence[_spc.SinglePipeConnection],  # type: ignore[name-defined]
    loopName: str,
    connectionsDefinitionMode: _cdm.ConnectionsDefinitionMode,
) -> None:
    for connection in connections:
        _setConnectionPropertiesForDefinitionMode(connection, loopName, connectionsDefinitionMode)


def setConnectionPropertiesForLoopWideDefaults(
    connections: _tp.Sequence[_spc.SinglePipeConnection],  # type: ignore[name-defined]
    loopName: str,
) -> None:
    for connection in connections:
        _setConnectionPropertiesForLoopWideDefaults(connection, loopName)


def _setConnectionPropertiesForDefinitionMode(
    connection: _spc.SinglePipeConnection, loopName: str, connectionsDefinitionMode: _cdm.ConnectionsDefinitionMode
) -> None:
    if connectionsDefinitionMode == _cdm.ConnectionsDefinitionMode.INDIVIDUAL:
        raise ValueError(
            "Cannot set connection loop-wide connection properties for definition mode.", connectionsDefinitionMode
        )

    if connectionsDefinitionMode == _cdm.ConnectionsDefinitionMode.LOOP_WIDE_DEFAULTS:
        _setConnectionPropertiesForLoopWideDefaults(connection, loopName)
    elif connectionsDefinitionMode == _cdm.ConnectionsDefinitionMode.DUMMY_PIPES:
        _setConnectionPropertiesForDummyPipe(connection)
    else:
        _tp.assert_never(connectionsDefinitionMode)


def _setConnectionPropertiesForLoopWideDefaults(
    connection: _spc.SinglePipeConnection, loopName: str  # type: ignore[name-defined]
) -> None:
    connection.lengthInM = _values.Variable(_names.getDefaultLengthName(loopName))
    connection.diameterInCm = _values.Variable(_names.getDefaultDiameterName(loopName))
    connection.uValueInWPerM2K = _values.Variable(_names.getDefaultUValueName(loopName))
    connection.shallBeSimulated = True


def _setConnectionPropertiesForDummyPipe(connection: _spc.SinglePipeConnection) -> None:
    connection.shallBeSimulated = False
