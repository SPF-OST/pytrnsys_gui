import collections.abc as _cabc
import dataclasses as _dc
import typing as _tp

import pytest as _pt

import pytrnsys.utils.result as _res
import trnsysGUI.connection.hydraulicExport.doublePipe.energyBalanceVariables as _ebv
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class _TestCase:
    variable: _ebv.EnergyBalanceVariables
    portItemType: _tp.Optional[_mfn.PortItemType]
    name: _res.Result[str]

    def testId(self) -> str:
        if not self.portItemType:
            return self.variable.name

        return f"{self.variable.name}/{self.portItemType.name}"


_TEST_CASES = [
    _TestCase(_ebv.EnergyBalanceVariables.CONVECTED, _mfn.PortItemType.COLD, "DTeeI_SCnrIColdConv"),
    _TestCase(_ebv.EnergyBalanceVariables.PIPE_TO_GRAVEL, _mfn.PortItemType.COLD, "DTeeI_SCnrIColdDiss"),
    _TestCase(_ebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE, _mfn.PortItemType.COLD, "DTeeI_SCnrIColdInt"),
    _TestCase(_ebv.EnergyBalanceVariables.CONVECTED, _mfn.PortItemType.HOT, "DTeeI_SCnrIHotConv"),
    _TestCase(_ebv.EnergyBalanceVariables.PIPE_TO_GRAVEL, _mfn.PortItemType.HOT, "DTeeI_SCnrIHotDiss"),
    _TestCase(_ebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE, _mfn.PortItemType.HOT, "DTeeI_SCnrIHotInt"),
    _TestCase(
        _ebv.EnergyBalanceVariables.CONVECTED,
        None,
        _res.Error("Energy balance variable `CONVECTED` is defined per single pipe."),
    ),
    _TestCase(
        _ebv.EnergyBalanceVariables.PIPE_TO_GRAVEL,
        None,
        _res.Error("Energy balance variable `PIPE_TO_GRAVEL` is defined per single pipe."),
    ),
    _TestCase(
        _ebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE,
        None,
        _res.Error("Energy balance variable `PIPE_INTERNAL_CHANGE` is defined per single pipe."),
    ),
    _TestCase(_ebv.EnergyBalanceVariables.COLD_TO_HOT, None, "DTeeI_SCnrIExch"),
    _TestCase(
        _ebv.EnergyBalanceVariables.COLD_TO_HOT,
        _mfn.PortItemType.COLD,
        _res.Error("Energy balance variable `COLD_TO_HOT` is not defined per single pipe."),
    ),
    _TestCase(
        _ebv.EnergyBalanceVariables.COLD_TO_HOT,
        _mfn.PortItemType.HOT,
        _res.Error("Energy balance variable `COLD_TO_HOT` is not defined per single pipe."),
    ),
    _TestCase(_ebv.EnergyBalanceVariables.GRAVEL_TO_SOIL, None, "DTeeI_SCnrIGrSl"),
    _TestCase(
        _ebv.EnergyBalanceVariables.GRAVEL_TO_SOIL,
        _mfn.PortItemType.COLD,
        _res.Error("Energy balance variable `GRAVEL_TO_SOIL` is not defined per single pipe."),
    ),
    _TestCase(
        _ebv.EnergyBalanceVariables.GRAVEL_TO_SOIL,
        _mfn.PortItemType.HOT,
        _res.Error("Energy balance variable `GRAVEL_TO_SOIL` is not defined per single pipe."),
    ),
    _TestCase(_ebv.EnergyBalanceVariables.SOIL_TO_FAR_FIELD, None, "DTeeI_SCnrISlFf"),
    _TestCase(
        _ebv.EnergyBalanceVariables.SOIL_TO_FAR_FIELD,
        _mfn.PortItemType.COLD,
        _res.Error("Energy balance variable `SOIL_TO_FAR_FIELD` is not defined per single pipe."),
    ),
    _TestCase(
        _ebv.EnergyBalanceVariables.SOIL_TO_FAR_FIELD,
        _mfn.PortItemType.HOT,
        _res.Error("Energy balance variable `SOIL_TO_FAR_FIELD` is not defined per single pipe."),
    ),
    _TestCase(_ebv.EnergyBalanceVariables.SOIL_INTERNAL_CHANGE, None, "DTeeI_SCnrISlInt"),
    _TestCase(
        _ebv.EnergyBalanceVariables.SOIL_INTERNAL_CHANGE,
        _mfn.PortItemType.COLD,
        _res.Error("Energy balance variable `SOIL_INTERNAL_CHANGE` is not defined per single pipe."),
    ),
    _TestCase(
        _ebv.EnergyBalanceVariables.SOIL_INTERNAL_CHANGE,
        _mfn.PortItemType.HOT,
        _res.Error("Energy balance variable `SOIL_INTERNAL_CHANGE` is not defined per single pipe."),
    ),
]


def _getVariableName(variable: _ebv.EnergyBalanceVariables) -> str:
    return variable.name


class TestEnergyBalanceVariables:
    @_pt.mark.parametrize("testCase", _TEST_CASES, ids=_TestCase.testId)
    def testVariableNameGenerator(self, testCase: _TestCase) -> None:
        generator = _ebv.VariableNameGenerator("DTeeI_SCnrI", coldPipeName="Cold", hotPipeName="Hot")

        name = None
        actualErrorMessage = None
        try:
            name = generator.getName(testCase.variable, testCase.portItemType)
        except ValueError as valueError:
            actualErrorMessage = str(valueError)

        if _res.isError(testCase.name):
            expectedErrorMessage = _res.error(testCase.name).message
            assert expectedErrorMessage == actualErrorMessage
        else:
            assert name == testCase.name

    @_pt.mark.parametrize("variable", _ebv.EnergyBalanceVariables, ids=_getVariableName)
    def testPortItemTypeStandardRaises(self, variable: _ebv.EnergyBalanceVariables) -> None:
        expectedErrorMessageRegexPattern = (
            r"^Energy balance variables are only defined for `COLD` or `HOT` port item types or `None`.$"
        )

        generator = _ebv.VariableNameGenerator("DTeeI_SCnrI", coldPipeName="Cold", hotPipeName="Hot")

        with _pt.raises(ValueError, match=expectedErrorMessageRegexPattern):
            generator.getName(variable, _mfn.PortItemType.STANDARD)

    def testThatAllVariablesAreTested(self) -> None:
        expectedPortItemTypes = {_mfn.PortItemType.COLD, _mfn.PortItemType.HOT, None}
        expectedPortItemTypesByVariable = {v: expectedPortItemTypes for v in _ebv.EnergyBalanceVariables}

        portItemTypesByVariable = self._getPortItemTypesByVariable()

        assert portItemTypesByVariable == expectedPortItemTypesByVariable

    @staticmethod
    def _getPortItemTypesByVariable() -> _cabc.Mapping[
        _ebv.EnergyBalanceVariables, set[_tp.Optional[_mfn.PortItemType]]
    ]:
        portItemTypesByVariable = dict[_ebv.EnergyBalanceVariables, set[_tp.Optional[_mfn.PortItemType]]]()
        for testCase in _TEST_CASES:
            portItemTypes = portItemTypesByVariable.get(testCase.variable, set())
            portItemTypes.add(testCase.portItemType)
            portItemTypesByVariable[testCase.variable] = portItemTypes

        return portItemTypesByVariable
