import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _dpc

from trnsysGUI.connection import values as _values

from . import _getEnergyBalanceVariables as _vars


def exportSimulatedConnection(doublePipeConnection, unitNumber):
    headerAndParameters = _getHeaderAndParameters(doublePipeConnection, unitNumber)
    inputs = _getInputs(doublePipeConnection)
    equations = _getEquations(doublePipeConnection, unitNumber)
    unitText = headerAndParameters + inputs + equations
    nextUnitNumber = unitNumber + 1
    return unitText, nextUnitNumber


def _getHeaderAndParameters(connection: _dpc.DoublePipeConnection, unitNumber: int) -> str:
    lengthInM = _values.getConvertedValueOrName(connection.lengthInM)
    headerAndParameters = f"""\
UNIT {unitNumber} TYPE 9511
! {connection.displayName}
PARAMETERS 36
****** pipe and soil properties ******
{lengthInM}                                ! Length of buried pipe, m
dpDiamIn                                ! Inner diameter of pipes, m
dpDiamOut                               ! Outer diameter of pipes, m
dpLambda                                ! Thermal conductivity of pipe material, kJ/(h*m*K)
dpDepth                                 ! Buried pipe depth, m
dpDiamCase                              ! Diameter of casing material, m
dpLambdaFill                            ! Thermal conductivity of fill insulation, kJ/(h*m*K)
dpDistPtoP                              ! Center-to-center pipe spacing, m
dpLambdaGap                             ! Thermal conductivity of gap material, kJ/(h*m*K)
dpGapThick                              ! Gap thickness, m
****** fluid properties ******
dpRhoFlu                                ! Density of fluid, kg/m^3
dpLambdaFl                              ! Thermal conductivity of fluid, kJ/(h*m*K)
dpCpFl                                  ! Specific heat of fluid, kJ/(kg*K)
dpViscFl                                ! Viscosity of fluid, kg/(m*h)
****** initial conditions ******
dpTIniCold                              ! Initial fluid temperature - Pipe cold, deg C
dpTIniHot                               ! Initial fluid temperature - Pipe hot, deg C
****** thermal properties soil ******
dpLamdaSl                               ! Thermal conductivity of soil, kJ/(h*m*K)
dpRhoSl                                 ! Density of soil, kg/m^3
dpCpSl                                  ! Specific heat of soil, kJ/(kg*K)
****** general temperature dependency (dependent on weather data) ******
TambAvg                                 ! Average surface temperature, deg C
dTambAmpl                               ! Amplitude of surface temperature, deg C
ddTcwOffset                             ! Days of minimum surface temperature
****** definition of nodes ******
dpNrFlNds                               ! Number of fluid nodes
dpNrSlRad                               ! Number of radial soil nodes
dpNrSlAx                                ! Number of axial soil nodes
dpNrSlCirc                              ! Number of circumferential soil nodes
dpRadNdDist                             ! Radial distance of node 1, m
dpRadNdDist                             ! Radial distance of node 2, m
dpRadNdDist                             ! Radial distance of node 3, m
dpRadNdDist                             ! Radial distance of node 4, m
dpRadNdDist                             ! Radial distance of node 5, m
dpRadNdDist                             ! Radial distance of node 6, m
dpRadNdDist                             ! Radial distance of node 7, m
dpRadNdDist                             ! Radial distance of node 8, m
dpRadNdDist                             ! Radial distance of node 9, m
dpRadNdDist                             ! Radial distance of node 10, m

"""
    return headerAndParameters


def _getInputs(connectionNames: _dpc.DoublePipeConnection) -> str:
    coldPipe = connectionNames.coldPipe
    hotPipe = connectionNames.hotPipe

    inputs = f"""\
INPUTS 6
{coldPipe.inputPort.inputTemperatureVariableName} ! Inlet fluid temperature - cold pipe, deg C
{coldPipe.inputPort.massFlowRateVariableName} ! Inlet fluid flow rate - cold pipe, kg/h
{coldPipe.outputPort.inputTemperatureVariableName} ! ! Other side of pipe - cold pipe, deg C
{hotPipe.inputPort.inputTemperatureVariableName} ! Inlet fluid temperature - hot pipe, deg C
{hotPipe.inputPort.massFlowRateVariableName} ! Inlet fluid flow rate - hot pipe, kg/h
{hotPipe.outputPort.inputTemperatureVariableName} ! ! Other side of pipe - hot pipe, deg C
*** initial values
dpTIniCold
0
dpTIniCold
dpTIniHot
0
dpTIniHot

"""
    return inputs


def _getEquations(
    doublePipeConnection: _dpc.DoublePipeConnection,
    unitNumber: int,
) -> str:
    energyBalanceVariables = _vars.getEnergyBalanceVariables(
        doublePipeConnection.displayName,
        coldPipeName=doublePipeConnection.coldPipe.name,
        hotPipeName=doublePipeConnection.hotPipe.name,
    )

    formattedEnergyBalanceVariables = "\n".join(
        f"{v.name} = [{unitNumber},{v.outputNumber}]*{v.conversionFactor} ! {v.comment}" for v in energyBalanceVariables
    )
    coldPipe = doublePipeConnection.coldPipe
    coldOutputTemperature = doublePipeConnection.getOutputTemperatureVariableName(coldPipe)
    coldCanonicalMassFlowRate = doublePipeConnection.getCanonicalMassFlowRateVariableName(coldPipe)

    hotPipe = doublePipeConnection.hotPipe
    hotOutputTemperature = doublePipeConnection.getOutputTemperatureVariableName(hotPipe)
    hotCanonicalMassFlow = doublePipeConnection.getCanonicalMassFlowRateVariableName(hotPipe)

    equations = f"""\
EQUATIONS {4 + len(energyBalanceVariables)}
{coldOutputTemperature} = [{unitNumber},1]  ! Outlet fluid temperature, deg C
{coldCanonicalMassFlowRate} = {coldPipe.inputPort.massFlowRateVariableName}  ! Outlet mass flow rate, kg/h

{hotOutputTemperature} = [{unitNumber},3]  ! Outlet fluid temperature, deg C
{hotCanonicalMassFlow} = {hotPipe.inputPort.massFlowRateVariableName}  ! Outlet mass flow rate, kg/h

{formattedEnergyBalanceVariables}

"""
    return equations
