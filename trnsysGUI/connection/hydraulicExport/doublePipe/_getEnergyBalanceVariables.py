import typing as _tp

import trnsysGUI.massFlowSolver.networkModel as _mfn

from . import energyBalanceVariables as _ebv


class EnergyBalanceVariablesFactory:
    def __init__(self, nameGenerator: _ebv.VariableNameGenerator):
        self._nameGenerator = nameGenerator

    def create(self) -> _tp.Sequence[_ebv.EnergyBalanceVariable]:
        return [
            self._createVariable(
                _ebv.EnergyBalanceVariables.CONVECTED,
                _mfn.PortItemType.COLD,
                7,
                "Convected heat [kW]",
                conversionFactor="-1*1/3600",
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE,
                _mfn.PortItemType.COLD,
                9,
                "Change in fluid's internal heat content compared to previous time step [kW]",
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.PIPE_TO_GRAVEL,
                _mfn.PortItemType.COLD,
                11,
                "Dissipated heat to casing (aka gravel) [kW]",
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.CONVECTED,
                _mfn.PortItemType.HOT,
                8,
                "Convected heat [kW]",
                conversionFactor="-1*1/3600",
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE,
                _mfn.PortItemType.HOT,
                10,
                "Change in fluid's internal heat content compared to previous time step [kW]",
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.PIPE_TO_GRAVEL,
                _mfn.PortItemType.HOT,
                12,
                "Dissipated heat to casing (aka gravel) [kW]",
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.COLD_TO_HOT, None, 13, "Dissipated heat from cold pipe to hot pipe [kW]"
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.GRAVEL_TO_SOIL, None, 14, "Dissipated heat from gravel to soil [kW]"
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.SOIL_TO_FAR_FIELD, None, 15, 'Dissipated heat from soil to "far field" [kW]'
            ),
            self._createVariable(
                _ebv.EnergyBalanceVariables.SOIL_INTERNAL_CHANGE,
                None,
                16,
                "Change in soil's internal heat content compared to previous time step [kW]",
            ),
        ]

    def _createVariable(
        self,
        variable: _ebv.EnergyBalanceVariables,
        portItemType: _tp.Optional[_mfn.PortItemType],
        outputNumber: int,
        comment: str,
        conversionFactor: str = "1/3600",
    ) -> _ebv.EnergyBalanceVariable:
        variableName = self._nameGenerator.getName(variable, portItemType)
        return _ebv.EnergyBalanceVariable(variableName, outputNumber, conversionFactor, comment)


def getEnergyBalanceVariables(
    doublePipeDisplayName: str, *, coldPipeName: str, hotPipeName: str
) -> _tp.Sequence[_ebv.EnergyBalanceVariable]:
    nameGenerator = _ebv.VariableNameGenerator(
        doublePipeDisplayName, coldPipeName=coldPipeName, hotPipeName=hotPipeName
    )

    variablesFactory = EnergyBalanceVariablesFactory(nameGenerator)

    energyBalanceVariables = variablesFactory.create()

    return energyBalanceVariables
