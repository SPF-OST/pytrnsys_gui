import typing as _tp

import trnsysGUI.connection.names as _cnames
import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.connection.hydraulicExport.doublePipe.energyBalanceVariables as _dpebv
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


def getDoublePipeEnergyBalanceEquations(hasInternalPipings: _tp.Sequence[_ip.HasInternalPiping]):
    simulatedDoublePipes = [
        ip for ip in hasInternalPipings if isinstance(ip, _dpc.DoublePipeConnection) and ip.shallBeSimulated
    ]

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
            coldPipeName=doublePipe.coldModelPipe.name,
            hotPipeName=doublePipe.hotModelPipe.name,
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
    Totals = _cnames.EnergyBalanceTotals.DoublePipe
    equations = f"""\
*** Double pipe energy balance
EQUATIONS 5
{Totals.CONVECTED} = {summedConvectedHeatFluxes}
{Totals.DISSIPATION_TO_FAR_FIELD} = {summedDissipationToFarField}
{Totals.PIPE_INTERNAL_CHANGE} = {summedPipeInternalEnergyChanges}
{Totals.SOIL_INTERNAL_CHANGE} = {summedSoilInternalEnergyChanges}
{Totals.IMBALANCE} = {Totals.CONVECTED} - {Totals.DISSIPATION_TO_FAR_FIELD}  - {Totals.PIPE_INTERNAL_CHANGE} - {Totals.SOIL_INTERNAL_CHANGE}
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
