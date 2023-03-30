import dataclasses as _dc
import typing as _tp

import trnsysGUI.connection.names as _cnames
import trnsysGUI.connection.hydraulicExport.doublePipe.energyBalanceVariables as _dpebv
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass()
class DoublePipe:
    displayName: str
    coldPipeName: str
    hotPipeName: str
    shallBeSimulated: bool


def getDoublePipeEnergyBalanceEquations(doublePipes: _tp.Sequence[DoublePipe]):
    simulatedDoublePipes = [ip for ip in doublePipes if ip.shallBeSimulated]

    if not simulatedDoublePipes:
        return ""

    equations = _createEquations(simulatedDoublePipes)
    return equations


def _createEquations(simulatedDoublePipes):
    dissipatedHeatFluxesToFarField = []
    convectedHeatFluxes = []
    pipeInternalEnergyChanges = []
    soilInternalEnergyChanges = []
    for doublePipe in simulatedDoublePipes:
        energyBalanceVariableNameGenerator = _dpebv.VariableNameGenerator(
            doublePipe.displayName,
            coldPipeName=doublePipe.coldPipeName,
            hotPipeName=doublePipe.hotPipeName,
        )

        _getEquationTerms(
            convectedHeatFluxes,
            dissipatedHeatFluxesToFarField,
            energyBalanceVariableNameGenerator,
            pipeInternalEnergyChanges,
            soilInternalEnergyChanges,
        )
    summedConvectedHeatFluxes = " + ".join(convectedHeatFluxes)
    summedDissipationToFarField = " + ".join(dissipatedHeatFluxesToFarField)
    summedPipeInternalEnergyChanges = " + ".join(pipeInternalEnergyChanges)
    summedSoilInternalEnergyChanges = " + ".join(soilInternalEnergyChanges)
    totals = _cnames.EnergyBalanceTotals.DoublePipe
    equations = f"""\
*** Double pipe energy balance
EQUATIONS 5
{totals.CONVECTED} = {summedConvectedHeatFluxes}
{totals.DISSIPATION_TO_FAR_FIELD} = {summedDissipationToFarField}
{totals.PIPE_INTERNAL_CHANGE} = {summedPipeInternalEnergyChanges}
{totals.SOIL_INTERNAL_CHANGE} = {summedSoilInternalEnergyChanges}
{totals.IMBALANCE} = {totals.CONVECTED} - {totals.DISSIPATION_TO_FAR_FIELD}  - {totals.PIPE_INTERNAL_CHANGE} - {totals.SOIL_INTERNAL_CHANGE}
"""
    return equations


def _getEquationTerms(
    convectedHeatFluxes,
    dissipatedHeatFluxesToFarField,
    energyBalanceVariableNameGenerator,
    pipeInternalEnergyChanges,
    soilInternalEnergyChanges,
):
    coldConvectedHeatFlux = energyBalanceVariableNameGenerator.getName(
        _dpebv.EnergyBalanceVariables.CONVECTED, _mfn.PortItemType.COLD
    )
    hotConvectedHeatFlux = energyBalanceVariableNameGenerator.getName(
        _dpebv.EnergyBalanceVariables.CONVECTED, _mfn.PortItemType.HOT
    )
    convectedHeatFluxes.extend([coldConvectedHeatFlux, hotConvectedHeatFlux])
    dissipatedHeatFluxToFarField = energyBalanceVariableNameGenerator.getName(
        _dpebv.EnergyBalanceVariables.SOIL_TO_FAR_FIELD
    )
    dissipatedHeatFluxesToFarField.append(dissipatedHeatFluxToFarField)
    coldPipeInternalEnergyChange = energyBalanceVariableNameGenerator.getName(
        _dpebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE, _mfn.PortItemType.COLD
    )
    hotPipeInternalEnergyChange = energyBalanceVariableNameGenerator.getName(
        _dpebv.EnergyBalanceVariables.PIPE_INTERNAL_CHANGE, _mfn.PortItemType.HOT
    )
    pipeInternalEnergyChanges.extend([coldPipeInternalEnergyChange, hotPipeInternalEnergyChange])
    soilInternalEnergyChange = energyBalanceVariableNameGenerator.getName(
        _dpebv.EnergyBalanceVariables.SOIL_INTERNAL_CHANGE
    )
    soilInternalEnergyChanges.append(soilInternalEnergyChange)
