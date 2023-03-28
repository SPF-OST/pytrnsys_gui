import dataclasses as _dc
import typing as _tp

import trnsysGUI.connection.hydraulicExport.doublePipe.energyBalanceVariables as _ebv
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass(frozen=True, order=True)
class _NameResult:
    variable: _ebv.EnergyBalanceVariables
    portItemType: _tp.Optional[_mfn.PortItemType]
    name: str


_EXPECTED_NAME_RESULTS = [
    _NameResult(_ebv.EnergyBalanceVariables.CONVECTED, _mfn.PortItemType.COLD, "DTeeI_SCnrIColdConv"),
    _NameResult(_ebv.EnergyBalanceVariables.PIPE_TO_GRAVEL, _mfn.PortItemType.COLD, "DTeeI_SCnrIColdDiss"),
    _NameResult(_ebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE, _mfn.PortItemType.COLD, "DTeeI_SCnrIColdInt"),
    _NameResult(_ebv.EnergyBalanceVariables.COLD_TO_HOT, None, "DTeeI_SCnrIExch"),
    _NameResult(_ebv.EnergyBalanceVariables.GRAVEL_TO_SOIL, None, "DTeeI_SCnrIGrSl"),
    _NameResult(_ebv.EnergyBalanceVariables.CONVECTED, _mfn.PortItemType.HOT, "DTeeI_SCnrIHotConv"),
    _NameResult(_ebv.EnergyBalanceVariables.PIPE_TO_GRAVEL, _mfn.PortItemType.HOT, "DTeeI_SCnrIHotDiss"),
    _NameResult(_ebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE, _mfn.PortItemType.HOT, "DTeeI_SCnrIHotInt"),
    _NameResult(_ebv.EnergyBalanceVariables.SOIL_TO_FAR_FIELD, None, "DTeeI_SCnrISlFf"),
    _NameResult(_ebv.EnergyBalanceVariables.SOIL_INTERNAL_CHANGE, None, "DTeeI_SCnrISlInt"),
]


class TestEnergyBalanceVariables:
    def testVariableNameGenerator(self):
        generator = _ebv.VariableNameGenerator("DTeeI_SCnrI", coldPipeName="Cold", hotPipeName="Hot")

        nameResult = self._getAllVariableNames(generator)

        assert nameResult == _EXPECTED_NAME_RESULTS

    @staticmethod
    def _getAllVariableNames(generator: _ebv.VariableNameGenerator) -> _tp.Sequence[_NameResult]:
        nameResults = []
        for variable in _ebv.EnergyBalanceVariables:
            portItemTypes = [None, _mfn.PortItemType.COLD, _mfn.PortItemType.HOT]
            for portItemType in portItemTypes:
                try:
                    name = generator.getName(variable, portItemType)
                    nameResult = _NameResult(variable, portItemType, name)
                    nameResults.append(nameResult)
                except ValueError:
                    pass

        def getNameResultName(nameResult_: _NameResult) -> str:
            return nameResult_.name

        return sorted(nameResults, key=getNameResultName)
