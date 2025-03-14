from __future__ import annotations

import collections.abc as _cabc
import dataclasses as _dc
import typing as _tp

import trnsysGUI.placeHolderNames as _phn


@_dc.dataclass
class Variable:  # pylint: disable=too-many-instance-attributes
    tmfName: str
    definition: str | None
    order: int
    role: str
    roleOrder: int
    unit: str
    bounds: str
    defaultValue: float | int

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

RequiredVariable = Variable | Unset


@_dc.dataclass
class VariableNameBuilder:
    propertyName: str
    variableNamePrefix: str | None
    usePortInVariableName: bool

    def getVariableName(
        self, connectionName: str | None, portName: str
    ) -> str:
        if self.usePortInVariableName:
            qualifiedPortName = _phn.getQualifiedPortName(
                connectionName, portName
            )
            return f"{self.variableNamePrefix}{qualifiedPortName}"

        connectionNameOrEmpty = connectionName or ""

        return f"{self.variableNamePrefix}{connectionNameOrEmpty}"

    def getRhs(self, connectionName: str | None, portName: str) -> str:
        qualifiedPortName = _phn.getQualifiedPortName(connectionName, portName)
        return f"@{self.propertyName}({qualifiedPortName})"

    @staticmethod
    def _getConnectionNamePart(
        connectionName: str | None, shallCapitalize: bool
    ) -> str:
        connectionNamePart = connectionName or ""

        if shallCapitalize:
            connectionNamePart = connectionNamePart.capitalize()

        return connectionNamePart

    def _getPortNamePart(self, portName: str) -> str:
        capitalizedPortNameOrEmpty = (
            portName.capitalize() if self.usePortInVariableName else ""
        )
        return capitalizedPortNameOrEmpty


class AllVariableStringConstants:
    TEMPERATURE = VariableNameBuilder("temp", "T", usePortInVariableName=True)
    MASS_FLOW_RATE = VariableNameBuilder(
        "mfr", "M", usePortInVariableName=False
    )
    REVERSE_TEMPERATURE = VariableNameBuilder(
        "revtemp", None, usePortInVariableName=True
    )
    DENSITY = VariableNameBuilder("rho", "Rho", usePortInVariableName=False)
    HEAT_CAPACITY = VariableNameBuilder(
        "cp", "Cp", usePortInVariableName=False
    )


def _getSummaryLine(
    qualifiedPortName: str,
    variableStringConstants: VariableNameBuilder,
    variable: Variable | None | Unset,
    direction: _tp.Literal["input", "output"],
) -> str:
    if not isinstance(variable, Variable):
        return ""

    computedVariable = (
        f"@{variableStringConstants.propertyName}({qualifiedPortName})"
    )
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
            _getSummaryLine(
                qualifiedPortName,
                AllVariableStringConstants.DENSITY,
                self.density,
                "input",
            ),
            _getSummaryLine(
                qualifiedPortName,
                AllVariableStringConstants.HEAT_CAPACITY,
                self.heatCapacity,
                "input",
            ),
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
        return [
            *self.inputPort.allVariables,
            *self.outputPort.allVariables,
            *self.fluid.allVariables,
        ]

    @property
    def areAnyRequiredVariablesUnset(self) -> bool:
        return (
            self.inputPort.areAnyRequiredVariablesUnset
            or self.outputPort.areAnyRequiredVariablesUnset
            or self.fluid.areAnyRequiredVariablesUnset
        )

    def getSummary(self) -> str:
        qualifiedInputPortName = _getQualifiedPortName(
            self.name, self.inputPort.name
        )
        fluidSummary = self.fluid.getSummary(qualifiedInputPortName)
        inputPortSummary = self.inputPort.getSummary(self.name)
        outputPortSummary = self.outputPort.getSummary(self.name)

        subSummaries = _joinNonEmptyStringsWithNewLines(
            fluidSummary, inputPortSummary, outputPortSummary
        )

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

    qualifiedPortName = (
        f"{connectionName.capitalize()}{capitalizedPortName}"
        if connectionName
        else capitalizedPortName
    )

    return qualifiedPortName


def _getSetVariable(variable: Variable | Unset) -> Variable:
    if not isinstance(variable, Variable):
        raise ValueError("Required variable not set.")

    return variable


@_dc.dataclass
class InputPort:
    name: str
    temperature: "RequiredVariable" = UNSET
    massFlowRate: "RequiredVariable" = UNSET

    @property
    def temperatureSet(self) -> Variable:
        return _getSetVariable(self.temperature)

    @property
    def massFlowRateSet(self) -> "Variable":
        return _getSetVariable(self.massFlowRate)

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return _removeUnsetAndNone(self.temperature, self.massFlowRate)

    @property
    def areAnyRequiredVariablesUnset(self) -> bool:
        return UNSET in (self.temperature, self.massFlowRate)

    def getSummary(self, connectionName: str | None) -> str:
        qualifiedPortName = _getQualifiedPortName(connectionName, self.name)
        summary = _joinNonEmptyStringsWithNewLines(
            _getSummaryLine(
                qualifiedPortName,
                AllVariableStringConstants.MASS_FLOW_RATE,
                self.massFlowRate,
                "input",
            ),
            _getSummaryLine(
                qualifiedPortName,
                AllVariableStringConstants.TEMPERATURE,
                self.temperature,
                "input",
            ),
        )

        return summary


@_dc.dataclass
class OutputPort:
    name: str
    temperature: "RequiredVariable" = UNSET
    reverseTemperature: Variable | None = None

    @property
    def temperatureSet(self) -> Variable:
        return _getSetVariable(self.temperature)

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return _removeUnsetAndNone(self.temperature, self.reverseTemperature)

    @property
    def areAnyRequiredVariablesUnset(self):
        return self.temperature == UNSET

    def getSummary(self, connectionName: str | None) -> str:
        qualifiedPortName = _getQualifiedPortName(connectionName, self.name)
        summary = _joinNonEmptyStringsWithNewLines(
            _getSummaryLine(
                qualifiedPortName,
                AllVariableStringConstants.TEMPERATURE,
                self.temperature,
                "output",
            ),
            _getSummaryLine(
                qualifiedPortName,
                AllVariableStringConstants.REVERSE_TEMPERATURE,
                self.reverseTemperature,
                "input",
            ),
        )

        return summary


def _removeUnsetAndNone(
    *variables: Variable | Unset | None,
) -> _cabc.Sequence[Variable]:
    return [v for v in variables if isinstance(v, Variable)]


@_dc.dataclass
class VariablesByRole:
    parameters: _cabc.Sequence[Variable]
    inputs: _cabc.Sequence[Variable]
    outputs: _cabc.Sequence[Variable]

    @property
    def allVariables(self) -> _cabc.Sequence[Variable]:
        return [*self.parameters, *self.inputs, *self.outputs]
