import abc as _abc
import dataclasses as _dc
import typing as _tp

import trnsysGUI.connection.values as _values


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
