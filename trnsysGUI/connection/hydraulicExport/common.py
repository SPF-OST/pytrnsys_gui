import abc as _abc
import dataclasses as _dc
import typing as _tp

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.connection.values as _values
import trnsysGUI.internalPiping as _ip


@_dc.dataclass
class PortBase(_abc.ABC):
    inputTemperatureVariableName: str


@_dc.dataclass
class InputPort(PortBase):
    massFlowRateVariableName: str


@_dc.dataclass
class OutputPort(PortBase):
    pass


_T = _tp.TypeVar("_T")


@_dc.dataclass
class GenericConnection(_tp.Generic[_T]):
    hydraulicConnection: _T
    lengthInM: _values.Value
    shallBeSimulated: bool


_TPort = _tp.TypeVar("_TPort", bound=_pib.PortItemBase)


@_dc.dataclass
class AdjacentHasInternalPiping(_tp.Generic[_TPort]):
    """A "component" (i.e. a connection or block item) that shares a port with us"""

    hasInternalPiping: _ip.HasInternalPiping
    sharedPort: _TPort


def getAdjacentConnection(port: _TPort) -> AdjacentHasInternalPiping[_TPort]:
    return AdjacentHasInternalPiping(port.getConnection(), port)


def getAdjacentBlockItem(port: _TPort) -> AdjacentHasInternalPiping[_TPort]:
    return AdjacentHasInternalPiping(port.parent, port)


@_dc.dataclass
class HydraulicConnectionBase(_tp.Generic[_TPort], _abc.ABC):
    displayName: str
    fromAdjacentHasPiping: AdjacentHasInternalPiping[_TPort]
    toAdjacentHasPiping: AdjacentHasInternalPiping[_TPort]
