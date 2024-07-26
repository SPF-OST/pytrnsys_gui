from __future__ import annotations

import dataclasses as _dc
import typing as _tp
from collections import abc as _cabc


@_dc.dataclass
class Variable:
    tmfName: str
    order: int
    role: str
    roleOrder: int
    unit: str
    bounds: str
    defaultValue: _tp.Union[float, int]

    def getInfo(self, withRole: bool) -> str:
        roleOrEmpty = f"{self.role.capitalize()} " if withRole else ""
        info = f"{roleOrEmpty}{self.roleOrder}: {self.tmfName} [{self.unit}] ({self.bounds})"
        return info

    @property
    def info(self) -> str:
        return self.getInfo(withRole=False)


class Unset:
    pass


UNSET = Unset()

RequiredVariable = _tp.Union[Variable, Unset]


@_dc.dataclass
class Fluid:
    density: Variable | None = None
    heatCapacity: Variable | None = None

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return _removeUnsetAndNone(self.density, self.heatCapacity)


@_dc.dataclass
class Connection:
    name: str | None
    inputPort: "InputPort"
    outputPort: "OutputPort"
    fluid: "Fluid" = _dc.field(default_factory=Fluid)

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return [*self.inputPort.allVariables, *self.outputPort.allVariables, *self.fluid.allVariables]


@_dc.dataclass
class InputPort:
    name: str
    temperature: "RequiredVariable" = UNSET
    massFlowRate: "RequiredVariable" = UNSET

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return _removeUnsetAndNone(self.temperature, self.massFlowRate)


@_dc.dataclass
class OutputPort:
    name: str
    temperature: "RequiredVariable" = UNSET
    reverseTemperature: Variable | None = None

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return _removeUnsetAndNone(self.temperature, self.reverseTemperature)


def _removeUnsetAndNone(*variables: Variable) -> _cabc.Sequence[Variable]:
    return [v for v in variables if isinstance(v, Variable)]


@_dc.dataclass
class VariablesByRole:
    parameters: _cabc.Sequence[Variable]
    inputs: _cabc.Sequence[Variable]
    outputs: _cabc.Sequence[Variable]

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return [*self.parameters, *self.inputs, *self.outputs]
