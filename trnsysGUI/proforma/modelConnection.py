from __future__ import annotations

import dataclasses as _dc
import typing as _tp


@_dc.dataclass(frozen=True)
class Variable:
    name: str
    definition: str | None
    order: int


class Unset:
    pass


UNSET = Unset()

RequiredVariable = _tp.Union[Variable, Unset]


@_dc.dataclass(frozen=True)
class Fluid:
    density: Variable | None = None
    heatCapacity: Variable | None = None

    @staticmethod
    def empty() -> "Fluid":
        return Fluid()


@_dc.dataclass(frozen=True)
class Connection:
    name: str | None
    inputPort: "InputPort"
    outputPort: "OutputPort"
    fluid: "Fluid" = _dc.field(default_factory=Fluid.empty)


@_dc.dataclass(frozen=True)
class InputPort:
    name: str
    temperature: "RequiredVariable" = UNSET
    massFlowRate: "RequiredVariable" = UNSET


@_dc.dataclass(frozen=True)
class OutputPort:
    name: str
    temperature: "RequiredVariable" = UNSET
    reverseTemperature: Variable | None = None
