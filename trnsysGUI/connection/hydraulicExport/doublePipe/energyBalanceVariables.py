import dataclasses as _dc
import enum as _enum
import typing as _tp

import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class EnergyBalanceVariable:
    name: str
    outputNumber: int
    conversionFactor: str
    comment: str


@_dc.dataclass
class _EnergyBalanceVariablesValue:
    suffix: str
    isPerSinglePipe: bool


class EnergyBalanceVariables(_enum.Enum):
    PIPE_TO_GRAVEL = _EnergyBalanceVariablesValue("Diss", True)
    CONVECTED = _EnergyBalanceVariablesValue("Conv", True)
    PIPE_INTERNAL_CHANGE = _EnergyBalanceVariablesValue("Int", True)
    COLD_TO_HOT = _EnergyBalanceVariablesValue("Exch", False)
    GRAVEL_TO_SOIL = _EnergyBalanceVariablesValue("GrSl", False)
    SOIL_TO_FAR_FIELD = _EnergyBalanceVariablesValue("SlFf", False)
    SOIL_INTERNAL_CHANGE = _EnergyBalanceVariablesValue("SlInt", False)


@_dc.dataclass
class VariableNameGenerator:
    def __init__(self, doublePipeDisplayName: str, *, coldPipeName: str, hotPipeName: str) -> None:
        self.doublePipeDisplayName = doublePipeDisplayName
        self.coldPipeName = coldPipeName
        self.hotPipeName = hotPipeName

    def getName(
        self,
        variable: EnergyBalanceVariables,
        portItemType: _tp.Optional[_mfn.PortItemType] = None,
    ) -> str:
        variableValue = variable.value
        prefix = self._getEnergyBalanceVariablePrefix(variable, portItemType)
        variableName = f"{prefix}{variableValue.suffix}"
        return variableName

    def _getEnergyBalanceVariablePrefix(
        self, variable: EnergyBalanceVariables, portItemType: _tp.Optional[_mfn.PortItemType]
    ) -> str:
        isPerSinglePipe = variable.value.isPerSinglePipe
        if not isPerSinglePipe and portItemType:
            raise ValueError(f"Energy balance variable `{variable.name}` is not defined per double pipe.")

        if isPerSinglePipe and not portItemType:
            raise ValueError(f"Energy balance variable `{variable.name}` is not defined per single pipe.")

        if not portItemType:
            return self.doublePipeDisplayName

        assert portItemType in [_mfn.PortItemType.COLD, _mfn.PortItemType.HOT]
        pipeName = self.coldPipeName if portItemType == _mfn.PortItemType.COLD else self.hotPipeName
        return f"{self.doublePipeDisplayName}{pipeName}"
