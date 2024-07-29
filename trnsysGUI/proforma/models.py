from __future__ import annotations

import collections.abc as _cabc
import dataclasses as _dc
import typing as _tp


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


@_dc.dataclass(frozen=True)
class Unset:
    pass


UNSET = Unset()

RequiredVariable = _tp.Union[Variable, Unset]


@_dc.dataclass
class VariableStringConstants:
    propertyName: str
    variableNamePrefix: str | None


class AllVariableStringConstants:
    TEMPERATURE = VariableStringConstants("temp", "T")
    MASS_FLOW_RATE = VariableStringConstants("mfr", "M")
    REVERSE_TEMPERATURE = VariableStringConstants("revtemp", None)
    DENSITY = VariableStringConstants("rho", "Rho")
    HEAT_CAPACITY = VariableStringConstants("cp", "Cp")


def _getSummaryLine(
    qualifiedPortName: str,
    variableStringConstants: VariableStringConstants,
    variable: Variable | None | Unset,
    direction: _tp.Literal["input", "output"],
) -> str:
    if not variable or variable == UNSET:
        return ""

    computedVariable = f"@{variableStringConstants.propertyName}({qualifiedPortName})"
    summaryLine = (
        f'"{variable.tmfName}" = {computedVariable}'
        if direction == "input"
        else f'{computedVariable} = "{variable.tmfName}"'
    )

    return summaryLine


def _joinNonEmptyStringsWithNewLines(*strings: str) -> str:
    nonEmptyStrings = [s for s in strings if s]
    return "\n".join(nonEmptyStrings)


@_dc.dataclass
class Fluid:
    density: Variable | None = None
    heatCapacity: Variable | None = None

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return _removeUnsetAndNone(self.density, self.heatCapacity)

    @property
    def areAnyRequiredVariablesUnset(self) -> bool:
        return False

    def getSummary(self, qualifiedPortName: str) -> str:
        summary = _joinNonEmptyStringsWithNewLines(
            _getSummaryLine(qualifiedPortName, AllVariableStringConstants.DENSITY, self.density, "input"),
            _getSummaryLine(qualifiedPortName, AllVariableStringConstants.HEAT_CAPACITY, self.heatCapacity, "input"),
        )

        return summary


@_dc.dataclass
class Connection:
    name: str | None
    inputPort: "InputPort"
    outputPort: "OutputPort"
    fluid: "Fluid" = _dc.field(default_factory=Fluid)

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return [*self.inputPort.allVariables, *self.outputPort.allVariables, *self.fluid.allVariables]

    @property
    def areAnyRequiredVariablesUnset(self) -> bool:
        return (
            self.inputPort.areAnyRequiredVariablesUnset
            or self.outputPort.areAnyRequiredVariablesUnset
            or self.fluid.areAnyRequiredVariablesUnset
        )

    def getSummary(self) -> str:
        qualifiedInputPortName = _getQualifiedPortName(self.name, self.inputPort.name)
        fluidSummary = self.fluid.getSummary(qualifiedInputPortName)
        inputPortSummary = self.inputPort.getSummary(self.name)
        outputPortSummary = self.outputPort.getSummary(self.name)

        subSummaries = _joinNonEmptyStringsWithNewLines(fluidSummary, inputPortSummary, outputPortSummary)

        if not subSummaries:
            return ""

        connectionName = self.name if self.name else "Default connection"
        summary = f"""\
** {connectionName}
{subSummaries}

"""
        return summary


def _getQualifiedPortName(connectionName: str | None, portName: str) -> str:
    capitalizedPortName = portName.capitalize()

    qualifiedPortName = f"{connectionName.capitalize()}{capitalizedPortName}" if connectionName else capitalizedPortName

    return qualifiedPortName


@_dc.dataclass
class InputPort:
    name: str
    temperature: "RequiredVariable" = UNSET
    massFlowRate: "RequiredVariable" = UNSET

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return _removeUnsetAndNone(self.temperature, self.massFlowRate)

    @property
    def areAnyRequiredVariablesUnset(self) -> bool:
        return self.temperature == UNSET or self.massFlowRate == UNSET

    def getSummary(self, connectionName: str | None) -> str:
        qualifiedPortName = _getQualifiedPortName(connectionName, self.name)
        summary = _joinNonEmptyStringsWithNewLines(
            _getSummaryLine(qualifiedPortName, AllVariableStringConstants.MASS_FLOW_RATE, self.massFlowRate, "input"),
            _getSummaryLine(qualifiedPortName, AllVariableStringConstants.TEMPERATURE, self.temperature, "input"),
        )

        return summary


@_dc.dataclass
class OutputPort:
    name: str
    temperature: "RequiredVariable" = UNSET
    reverseTemperature: Variable | None = None

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return _removeUnsetAndNone(self.temperature, self.reverseTemperature)

    @property
    def areAnyRequiredVariablesUnset(self):
        return self.temperature == UNSET

    def getSummary(self, connectionName: str | None) -> str:
        qualifiedPortName = _getQualifiedPortName(connectionName, self.name)
        summary = _joinNonEmptyStringsWithNewLines(
            _getSummaryLine(qualifiedPortName, AllVariableStringConstants.TEMPERATURE, self.temperature, "output"),
            _getSummaryLine(
                qualifiedPortName, AllVariableStringConstants.REVERSE_TEMPERATURE, self.reverseTemperature, "input"
            ),
        )

        return summary


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
