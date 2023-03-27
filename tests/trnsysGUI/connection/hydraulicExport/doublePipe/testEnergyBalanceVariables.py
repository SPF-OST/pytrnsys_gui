import typing as _tp

import trnsysGUI.connection.hydraulicExport.doublePipe.energyBalanceVariables as _ebv
import trnsysGUI.massFlowSolver.networkModel as _mfn

_EXPECTED_NAMES = """\
DTeeI_SCnrIColdConv
DTeeI_SCnrIColdDiss
DTeeI_SCnrIColdInt
DTeeI_SCnrIExch
DTeeI_SCnrIGrSl
DTeeI_SCnrIHotConv
DTeeI_SCnrIHotDiss
DTeeI_SCnrIHotInt
DTeeI_SCnrISlFf
DTeeI_SCnrISlInt"""


class TestEnergyBalanceVariables:
    def testVariableNameGenerator(self):
        generator = _ebv.VariableNameGenerator("DTeeI_SCnrI", coldPipeName="Cold", hotPipeName="Hot")

        names = self._getAllVariableNames(generator)

        assert "\n".join(names) == _EXPECTED_NAMES

    @staticmethod
    def _getAllVariableNames(generator: _ebv.VariableNameGenerator) -> _tp.Sequence[str]:
        names = []
        for variable in _ebv.EnergyBalanceVariables:
            portItemTypes = [None, _mfn.PortItemType.COLD, _mfn.PortItemType.HOT]
            for portItemType in portItemTypes:
                try:
                    name = generator.getName(variable, portItemType)
                    names.append(name)
                except ValueError:
                    pass

        return sorted(names)
