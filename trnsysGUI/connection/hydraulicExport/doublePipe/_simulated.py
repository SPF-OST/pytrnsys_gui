import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _dpc
import trnsysGUI.globalNames as _gnames

from . import _getEnergyBalanceVariables as _vars


def exportSimulatedConnection(doublePipeConnection: _dpc.ExportDoublePipeConnection, unitNumber):
    constants = _getConstants(doublePipeConnection)
    headerAndParameters = _getHeaderAndParameters(doublePipeConnection, unitNumber)
    hydraulicConnection = doublePipeConnection.hydraulicConnection
    inputs = _getInputs(hydraulicConnection)
    equations = _getEquations(hydraulicConnection, unitNumber)
    unitText = constants + headerAndParameters + inputs + equations
    nextUnitNumber = unitNumber + 1
    return unitText, nextUnitNumber


def _getNCircumferentialSoilNodes(displayName: str) -> str:
    nCircularSoilNodesName = f"{displayName}_NrSlCirc"
    return nCircularSoilNodesName


def _getNFluidNodesName(displayName: str) -> str:
    nFluidNodesName = f"{displayName}_NrFlNds"
    return nFluidNodesName


def _getNAxialSoilNodesName(displayName: str) -> str:
    nAxialSoilNodesName = f"{displayName}_NrSlAx"
    return nAxialSoilNodesName


def _getPipeLengthName(displayName: str) -> str:
    pipeLengthName = f"{displayName}_Len"
    return pipeLengthName


def _getConstants(connection: _dpc.ExportDoublePipeConnection) -> str:
    names = _gnames.DoublePipes
    displayName = connection.hydraulicConnection.displayName
    nAxialSoilNodesReference = names.N_AXIAL_SOIL_NODES_AT_REFERENCE_LENGTH

    pipeLengthName = _getPipeLengthName(displayName)
    nAxialSoilNodesName = _getNAxialSoilNodesName(displayName)
    nFluidNodesName = _getNFluidNodesName(displayName)
    nCircumferentialSoilNodes = _getNCircumferentialSoilNodes(displayName)

    constants = f"""\
CONSTANTS 4
{pipeLengthName} = {connection.lengthInM}
! Round up to smallest larger integer
{nAxialSoilNodesName} = INT({pipeLengthName}*{nAxialSoilNodesReference}/{names.REFERENCE_LENGTH}) + 1
{nFluidNodesName} = {names.FLUID_TO_SOIL_NODES_RATIO}*{nAxialSoilNodesName}
{nCircumferentialSoilNodes} = {names.N_CIRCUMFERENTIAL_SOIL_NODES}

"""
    return constants


def _getHeaderAndParameters(connection: _dpc.ExportDoublePipeConnection, unitNumber: int) -> str:
    displayName = connection.hydraulicConnection.displayName

    pipeLengthName = _getPipeLengthName(displayName)
    nFluidNodesName = _getNFluidNodesName(displayName)
    nAxialSoilNodesName = _getNAxialSoilNodesName(displayName)
    nCircularSoilNodesName = _getNCircumferentialSoilNodes(displayName)

    headerAndParameters = f"""\
UNIT {unitNumber} TYPE 9511
! {displayName}
PARAMETERS 36
****** pipe and soil properties ******
{pipeLengthName}                        ! Length of buried pipe, m
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
{_gnames.DoublePipes.INITIAL_COLD_TEMPERATURE.ljust(39)} ! Initial fluid temperature - Pipe cold, deg C
{_gnames.DoublePipes.INITIAL_HOT_TEMPERATURE.ljust(39)} ! Initial fluid temperature - Pipe hot, deg C
****** thermal properties soil ******
dpLamdaSl                               ! Thermal conductivity of soil, kJ/(h*m*K)
dpRhoSl                                 ! Density of soil, kg/m^3
dpCpSl                                  ! Specific heat of soil, kJ/(kg*K)
****** general temperature dependency (dependent on weather data) ******
TambAvg                                 ! Average surface temperature, deg C
dTambAmpl                               ! Amplitude of surface temperature, deg C
ddTcwOffset                             ! Days of minimum surface temperature
****** definition of nodes ******
{nFluidNodesName}                       ! Number of fluid nodes
dpNrSlRad                               ! Number of radial soil nodes
{nAxialSoilNodesName}                   ! Number of axial soil nodes
{nCircularSoilNodesName}                ! Number of circumferential soil nodes
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


def _getInputs(hydraulicConnection: _dpc.ExportHydraulicDoublePipeConnection) -> str:
    coldPipe = hydraulicConnection.coldPipe
    hotPipe = hydraulicConnection.hotPipe

    inputs = f"""\
INPUTS 6
{coldPipe.inputPort.inputTemperatureVariableName} ! Inlet fluid temperature - cold pipe, deg C
{coldPipe.inputPort.massFlowRateVariableName} ! Inlet fluid flow rate - cold pipe, kg/h
{coldPipe.outputPort.inputTemperatureVariableName} ! ! Other side of pipe - cold pipe, deg C
{hotPipe.inputPort.inputTemperatureVariableName} ! Inlet fluid temperature - hot pipe, deg C
{hotPipe.inputPort.massFlowRateVariableName} ! Inlet fluid flow rate - hot pipe, kg/h
{hotPipe.outputPort.inputTemperatureVariableName} ! ! Other side of pipe - hot pipe, deg C
*** initial values
{_gnames.DoublePipes.INITIAL_COLD_TEMPERATURE}
0
{_gnames.DoublePipes.INITIAL_COLD_TEMPERATURE}
{_gnames.DoublePipes.INITIAL_HOT_TEMPERATURE}
0
{_gnames.DoublePipes.INITIAL_HOT_TEMPERATURE}

"""
    return inputs


def _getEquations(
    hydraulicConnection: _dpc.ExportHydraulicDoublePipeConnection,
    unitNumber: int,
) -> str:
    energyBalanceVariables = _vars.getEnergyBalanceVariables(
        hydraulicConnection.displayName,
        coldPipeName=hydraulicConnection.coldPipe.name,
        hotPipeName=hydraulicConnection.hotPipe.name,
    )

    formattedEnergyBalanceVariables = "\n".join(
        f"{v.name} = [{unitNumber},{v.outputNumber}]*{v.conversionFactor} ! {v.comment}" for v in energyBalanceVariables
    )
    coldPipe = hydraulicConnection.coldPipe
    hotPipe = hydraulicConnection.hotPipe

    conn = hydraulicConnection
    equations = f"""\
EQUATIONS {4 + len(energyBalanceVariables)}
{conn.coldOutputTemperatureVariableName} = [{unitNumber},1]  ! Outlet fluid temperature, deg C
{conn.coldCanonicalMassFlowRateVariableName} = {coldPipe.inputPort.massFlowRateVariableName}  ! Outlet mass flow rate, kg/h

{conn.hotOutputTemperatureVariableName} = [{unitNumber},3]  ! Outlet fluid temperature, deg C
{conn.hotCanonicalMassFlowRateVariableName} = {hotPipe.inputPort.massFlowRateVariableName}  ! Outlet mass flow rate, kg/h

{formattedEnergyBalanceVariables}

"""
    return equations
