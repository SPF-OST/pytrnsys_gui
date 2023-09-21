import trnsysGUI.connection.hydraulicExport.common as _com
import trnsysGUI.connection.hydraulicExport.doublePipe as _he
import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _model

_SIMULATED_DOUBLE_PIPE_CONNECTION = _model.ExportDoublePipeConnection(
    _model.ExportHydraulicDoublePipeConnection(
        displayName="DTeeD_SCnrD",
        coldPipe=_model.Pipe(
            name="Cold",
            inputPort=_com.InputPort("TSCnrDCold", "MDTeeD_SCnrDCold_A"),
            outputPort=_com.OutputPort("TDTeeDCold"),
        ),
        hotPipe=_model.Pipe(
            name="Hot",
            inputPort=_com.InputPort("TDTeeDHot", "MDTeeD_SCnrDHot_A"),
            outputPort=_com.OutputPort("TSCnrDHot"),
        ),
    ),
    lengthInM=400.0,
    shallBeSimulated=True,
)

_EXPECTED_SIMULATED_UNIT_TEXT = """\
CONSTANTS 6
! Round down to largest smaller integer
DTeeD_SCnrDNrSlAxFrac = 400.0*dpNrSlAxRef/dpLengthRef
DTeeD_SCnrDNrSlAxRem = MOD(400.0*dpNrSlAxRef, dpLengthRef)
DTeeD_SCnrDNrSlAxCeil = MAX(DTeeD_SCnrDNrSlAxFrac - DTeeD_SCnrDNrSlAxRem, 1)
DTeeD_SCnrDNrSlAx = dpNrSlAxFactor*DTeeD_SCnrDNrSlAxCeil

DTeeD_SCnrDNrFlNds = dpNrFlNdsFactor*dpNrFlNdsToNrSlAxRatio*DTeeD_SCnrDNrSlAx
DTeeD_SCnrDNrSlCirc = dpNrSlCircFactor*dpNrSlCirc

UNIT 503 TYPE 9511
! DTeeD_SCnrD
PARAMETERS 36
****** pipe and soil properties ******
400.0                                ! Length of buried pipe, m
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
DTeeD_SCnrDNrFlNds                       ! Number of fluid nodes
dpNrSlRad                               ! Number of radial soil nodes
DTeeD_SCnrDNrSlAx                   ! Number of axial soil nodes
DTeeD_SCnrDNrSlCirc                ! Number of circumferential soil nodes
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

INPUTS 6
TSCnrDCold ! Inlet fluid temperature - cold pipe, deg C
MDTeeD_SCnrDCold_A ! Inlet fluid flow rate - cold pipe, kg/h
TDTeeDCold ! ! Other side of pipe - cold pipe, deg C
TDTeeDHot ! Inlet fluid temperature - hot pipe, deg C
MDTeeD_SCnrDHot_A ! Inlet fluid flow rate - hot pipe, kg/h
TSCnrDHot ! ! Other side of pipe - hot pipe, deg C
*** initial values
dpTIniCold
0
dpTIniCold
dpTIniHot
0
dpTIniHot

EQUATIONS 14
TDTeeD_SCnrDCold = [503,1]  ! Outlet fluid temperature, deg C
MDTeeD_SCnrDCold = MDTeeD_SCnrDCold_A  ! Outlet mass flow rate, kg/h

TDTeeD_SCnrDHot = [503,3]  ! Outlet fluid temperature, deg C
MDTeeD_SCnrDHot = MDTeeD_SCnrDHot_A  ! Outlet mass flow rate, kg/h

DTeeD_SCnrDColdConv = [503,7]*-1*1/3600 ! Convected heat [kW]
DTeeD_SCnrDColdInt = [503,9]*1/3600 ! Change in fluid's internal heat content compared to previous time step [kW]
DTeeD_SCnrDColdDiss = [503,11]*1/3600 ! Dissipated heat to casing (aka gravel) [kW]
DTeeD_SCnrDHotConv = [503,8]*-1*1/3600 ! Convected heat [kW]
DTeeD_SCnrDHotInt = [503,10]*1/3600 ! Change in fluid's internal heat content compared to previous time step [kW]
DTeeD_SCnrDHotDiss = [503,12]*1/3600 ! Dissipated heat to casing (aka gravel) [kW]
DTeeD_SCnrDExch = [503,13]*1/3600 ! Dissipated heat from cold pipe to hot pipe [kW]
DTeeD_SCnrDGrSl = [503,14]*1/3600 ! Dissipated heat from gravel to soil [kW]
DTeeD_SCnrDSlFf = [503,15]*1/3600 ! Dissipated heat from soil to "far field" [kW]
DTeeD_SCnrDSlInt = [503,16]*1/3600 ! Change in soil's internal heat content compared to previous time step [kW]

"""

_DUMMY_DOUBLE_PIPE_CONNECTION = _model.ExportDoublePipeConnection(
    _model.ExportHydraulicDoublePipeConnection(
        displayName="DTeeD_SCnrD",
        coldPipe=_model.Pipe(
            name="Cold",
            inputPort=_com.InputPort("TSCnrDCold", "MDTeeD_SCnrDCold_A"),
            outputPort=_com.OutputPort("TDTeeDCold"),
        ),
        hotPipe=_model.Pipe(
            name="Hot",
            inputPort=_com.InputPort("TDTeeDHot", "MDTeeD_SCnrDHot_A"),
            outputPort=_com.OutputPort("TSCnrDHot"),
        ),
    ),
    lengthInM=400.0,
    shallBeSimulated=False,
)

_EXPECTED_DUMMY_UNIT_TEXT = """\
! BEGIN DTeeD_SCnrD
! cold pipe
UNIT 503 TYPE 2221
PARAMETERS 2
mfrSolverAbsTol
dpTIniCold
INPUTS 3
MDTeeD_SCnrDCold_A TSCnrDCold TDTeeDCold
***
0 dpTIniCold dpTIniCold
EQUATIONS 2
TDTeeD_SCnrDCold = [503,1]
MDTeeD_SCnrDCold = MDTeeD_SCnrDCold_A

! hot pipe
UNIT 504 TYPE 2221
PARAMETERS 2
mfrSolverAbsTol
dpTIniHot
INPUTS 3
MDTeeD_SCnrDHot_A TDTeeDHot TSCnrDHot
***
0 dpTIniHot dpTIniHot
EQUATIONS 2
TDTeeD_SCnrDHot = [504,1]
MDTeeD_SCnrDHot = MDTeeD_SCnrDHot_A
! END DTeeD_SCnrD


"""


class TestDoublePipeConnection:
    def testSimulatedExport(self):
        actualUnitText, nextUnitNumber = _he.export(_SIMULATED_DOUBLE_PIPE_CONNECTION, 503)
        assert actualUnitText == _EXPECTED_SIMULATED_UNIT_TEXT
        assert nextUnitNumber == 504

    def testDummyExport(self):
        actualUnitText, nextUnitNumber = _he.export(
            _DUMMY_DOUBLE_PIPE_CONNECTION,
            503,
        )
        assert actualUnitText == _EXPECTED_DUMMY_UNIT_TEXT
        assert nextUnitNumber == 505
