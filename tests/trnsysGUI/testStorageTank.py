import cgitb as _cgitb
import json as _json
import logging as _log
import unittest.mock as _mock
import pathlib as _pl

from PyQt5 import QtWidgets as _widgets

import trnsysGUI.StorageTank as _st

# Sometimes PyQT crashes only returning with quite a cryptic error code. Sometimes, again, we can get
# a more helpful stack trace using the cgitb module.
_cgitb.enable(format="text")


class _StrictMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestStorageTank:
    LEGACY_JSON_PATH = _pl.Path(__file__).parent / "data" / "storageTankOldestFormat.json"

    def testDeserializeJsonFromLegacyFormatAndSerialize(self, tmp_path):  # pylint: disable=invalid-name
        expectedPath = _pl.Path(__file__).parent / "data" / "storageTankNewestFormat.json"
        expectedStorageTankJson = expectedPath.read_text()

        logger = _log.getLogger("root")
        (
            diagramViewMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, tmp_path)

        legacyJson = self.LEGACY_JSON_PATH.read_text()
        storageTank = self._deserializeStorageTank(legacyJson, diagramViewMock)

        serializedStorageTank = storageTank.encode()[1]
        actualStorageTankJson = _json.dumps(
            serializedStorageTank, indent=4, sort_keys=True
        )

        assert actualStorageTankJson == expectedStorageTankJson

        self._deserializeStorageTank(actualStorageTankJson, diagramViewMock)

    @staticmethod
    def _deserializeStorageTank(storageTankLegacyJson, diagramViewMock):
        legacySerializedStorageTank = _json.loads(storageTankLegacyJson)

        storageTank = _st.StorageTank(trnsysType="StorageTank", parent=diagramViewMock)  # pylint: disable=no-member
        diagramViewMock.scene().addItem(storageTank)

        blocks = []
        storageTank.decode(legacySerializedStorageTank, blocks)

        return storageTank

    def testExportDdck(self, tmp_path):  # pylint: disable=invalid-name
        logger = _log.getLogger("root")
        (
            diagramViewMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, tmp_path)

        legacyJson = self.LEGACY_JSON_PATH.read_text()
        storageTank = self._deserializeStorageTank(legacyJson, diagramViewMock)

        self._setupExternalConnectionMocks(storageTank)

        storageTank.exportDck()

        actualDdckPath = tmp_path / "ddck" / "StorageTank_7701" / "Dhw.ddck"
        actualDdckContent = actualDdckPath.read_text()
        print(actualDdckContent)

        expectedDdckContent = r"""*************************************
**BEGIN Dhw.ddck
*************************************

*************************************
** Plug-Flow Model exported from TRNSYS GUI
*************************************

*************************************
** To be checked: 
** check cp and rho values for the cirquits 
** default is cpwat and rhowat, for solarcirc usually cpbri and rhobri have to be used 
*************************************

*************************************
** outputs to energy balance in kWh
** Following this naming standard : qSysIn_name, qSysOut_name, elSysIn_name, elSysOut_name
*************************************
EQUATIONS 3
qSysOut_TesDhwLoss = sumQLoss_Tes7703
qSysOut_TesDhwAcum = sumQAcum_Tes7703
elSysIn_Q_TesDhwAux = qHeatSource_Tes7703

*************************************
*** Inputs from hydraulic solver ****
*************************************
EQUATIONS 3
Tdp1In_Tes7703 = Tdpp0ExtFromPortConn ! @connectDdck
Mfrdp1_Tes7703 = Mfrdpp0ExtFromPortConn ! @connectDdck
Tdp1InRev_Tes7703 = Tdpp0ExtToPortConn ! @connectDdck
EQUATIONS 3
Tdp2In_Tes7703 = Tdpp1ExtFromPortConn ! @connectDdck
Mfrdp2_Tes7703 = Mfrdpp1ExtFromPortConn ! @connectDdck
Tdp2InRev_Tes7703 = Tdpp1ExtToPortConn ! @connectDdck
EQUATIONS 3
Tdp3In_Tes7703 = Tdpp2ExtFromPortConn ! @connectDdck
Mfrdp3_Tes7703 = Mfrdpp2ExtFromPortConn ! @connectDdck
Tdp3InRev_Tes7703 = Tdpp2ExtToPortConn ! @connectDdck
EQUATIONS 3
Thx1In_Tes7703 = Thx0ExtFromPortConn ! @connectDdck
Mfrhx1_Tes7703 = Mfrhx0ExtFromPortConn ! @connectDdck
Thx1InRev_Tes7703 = Thx0ExtToPortConn ! @connectDdck
CONSTANTS 2
zAux1_Tes7703=0.00 !connectDDck
qAux1_Tes7703=0.00 !connectDDck

*************************************
**** Outputs to hydraulic solver ****
*************************************
EQUATIONS 3
*** direct port outputs
Tdp1Out_Tes7703=[50,1] ! 
Tdp2Out_Tes7703=[50,3] ! 
Tdp3Out_Tes7703=[50,5] ! 
EQUATIONS 1
*** heat exchanger outputs
Thx1Out_Tes7703=[50,102] ! 

*************************************
****** Parameters of Type1924 *******
*************************************
CONSTANTS 1
ratioTes7703 = Vol_Tes7703 / VStoreRef
*********Connecting values of DIRECT PORT=1***********
CONSTANTS 2
zInDp1_Tes7703=0.95 ! @connectDdck 
zOutDp1_Tes7703=0.35 ! @connectDdck 
*********Connecting values of DIRECT PORT=2***********
CONSTANTS 2
zInDp2_Tes7703=0.70 ! @connectDdck 
zOutDp2_Tes7703=0.90 ! @connectDdck 
*********Connecting values of DIRECT PORT=3***********
CONSTANTS 2
zInDp3_Tes7703=0.05 ! @connectDdck 
zOutDp3_Tes7703=0.95 ! @connectDdck 
*********Connecting values of HX=1***********
CONSTANTS 4
zInhx1_Tes7703=0.30  ! @connectDdck
zOuthx1_Tes7703=0.12 ! @connectDdck
Cphx1_Tes7703=cpwat     ! @connectDdck
Rhohx1_Tes7703=rhowat    ! @connectDdck
*********Constant of DIRECT PORT=1***********
CONSTANTS 1
Dp1Strat_Tes7703=0 ! 0: no forced stratification ; 1: force to stratify
*********Constant of DIRECT PORT=2***********
CONSTANTS 1
Dp2Strat_Tes7703=0 ! 0: no forced stratification ; 1: force to stratify
*********Constant of DIRECT PORT=3***********
CONSTANTS 1
Dp3Strat_Tes7703=0 ! 0: no forced stratification ; 1: force to stratify
********** HEAT EXCHANGER CONSTANTS*******
CONSTANTS 1
nHxUsed_Tes7703=1 
*********Constant values of HX=1***********
CONSTANTS 15
dInHx1_Tes7703=0.05 ! m only if modHx1=1
dOutHx1_Tes7703=0.06 ! m only if modHx1=1
LHx1_Tes7703=20 ! m only if modHx1=1
LamHx1_Tes7703=50 ! W/mK only if modHx1=1
brineConcHx1_Tes7703=30 ! [0-100] only if modHx1=1
VHx1_Tes7703=0. 
nCvHx1_Tes7703=20 
modHx1_Tes7703=1 ! modHX1, 0 = physical model, 1 = Drueck-model (Multiport)
nNuHx1_Tes7703=0.5 !  only if modHx1=1
cNuHx1_Tes7703=0.25 !  only if modHx1=1
dUaMfrHx1_Tes7703=0.375 ! only if modHx1=0
dUadTHx1_Tes7703=0.0 ! only if modHx1=0
dUaTHx1_Tes7703=0.458 ! only if modHx1=0
UaHx1_Tes7703=1105*ratioTes7703 ! kJ/hK only if modHx1=0
startUpHx1_Tes7703=0. ! only if modHx1=0
*************************************
** USER DEFINED TEMPERATURE SENSOR HEIGHTS. To be changed by user 
*************************************
CONSTANTS 10
zSen1_Tes7703=0.05
zSen2_Tes7703=0.15
zSen3_Tes7703=0.25
zSen4_Tes7703=0.35
zSen5_Tes7703=0.45
zSen6_Tes7703=0.55
zSen7_Tes7703=0.65
zSen8_Tes7703=0.75
zSen9_Tes7703=0.85
zSen10_Tes7703=0.95
*************************************
** USER DEFINED AVERAGED TEMPERATURE SENSOR HEIGHTS. To be changed by user 
*************************************
CONSTANTS 10
zSenAvgBot1_Tes7703 = 0.05
zSenAvgTop1_Tes7703 = 0.15
zSenAvgBot2_Tes7703 = 0.25
zSenAvgTop2_Tes7703 = 0.35
zSenAvgBot3_Tes7703 = 0.45
zSenAvgTop3_Tes7703 = 0.55
zSenAvgBot4_Tes7703 = 0.65
zSenAvgTop4_Tes7703 = 0.75
zSenAvgBot5_Tes7703 = 0.85
zSenAvgTop5_Tes7703 = 0.95
CONSTANTS 12
Vol_Tes7703=1          ! 1: m3, volume of store
RhoWat_Tes7703=RhoWat  ! 2: kg/m3, density of storage media
CpWat_Tes7703=CpWat    ! 3: kJ/kgK, specific heat of storage media
lamZ_Tes7703=0.6       ! 4: W/mK, effective vertical thermal conductivity of TES
Heigh_Tes7703=1.       ! 5: m, storage height
Tini_Tes7703=60.       ! 6: oC, initial temperature
nCvMax_Tes7703=400     ! 7: -, minimum relative plug height
nCvMin_Tes7703=20      ! 8: -, maximum relative plug height
maxTDiff_Tes7703=0.015 ! 9: K, maximum temperature difference between plugs
readMode_Tes7703=0     ! 10: 1: from table, 0: Tini and CapTot
Tref_Tes7703=273.15    ! 11: oC, reference temperature
Tmax_Tes7703=100.       ! 6: oC, initial temperature
CONSTANTS 10
Ufoam_Tes7703= 0.67 ! W/(m2K) 6 cm of foam of 0.04 W/(mK) 
Ubot_Tes7703 = 1.5 ! W/(m2K) 2 cm of foam of 0.04 W/(mK)
Atop_Tes7703 = Vol_Tes7703/Heigh_Tes7703 ! m2
Diameter_Tes7703 = (4*ATop_Tes7703/PI)^0.5 ! m 
ALat_Tes7703 = Heigh_Tes7703*PI*Diameter_Tes7703 ! m2
UaBot_Tes7703= Ubot_Tes7703*ATop_Tes7703 ! @userDefined W/k 
Uaz1_Tes7703 = Ufoam_Tes7703*ALat_Tes7703/3 ! @userDefined W/k
Uaz2_Tes7703 = Ufoam_Tes7703*ALat_Tes7703/3 ! @userDefined W/k
Uaz3_Tes7703 = Ufoam_Tes7703*ALat_Tes7703/3 ! @userDefined W/k
UaTop_Tes7703 = Ufoam_Tes7703*ATop_Tes7703 ! @userDefined W/k
************* MOVING PLATE *******************
CONSTANTS 4
MoInsPlate_Tes7703=0 ! 0-2, Insulation Plate Mode: 0 = no insulation plate inside TES, 1 = insulation plate at fixed relative height, 2 = insulation plate at fixed temperature / density controlled 
zInsPlate_Tes7703=0  ! 0-1, relative position of fixed height insulation plate inside TES (only for Insulation Plate Mode = 1
TinsPlate_Tes7703=0  ! oC, temperature at which moveable insulation plate floats in TES (only for Insulation Plate Mode = 2)
UAinsPlate_Tes7703=0 ! W/K, overall heat transfer coefficient across moveable insulation plate (including heat transfer in gap between plate and wall and in wall at the respective height)
*************************************
********** TYPE DEFINITION **********
*************************************
UNIT 50 TYPE 7704     ! plug flow tank
PARAMETERS 219 
Vol_Tes7703     ! 1: m3, volume of store
RhoWat_Tes7703  ! 2: kg/m3, density of storage media
CpWat_Tes7703   ! 3: kJ/kgK, specific heat of storage media
lamZ_Tes7703    ! 4: W/mK, effective vertical thermal conductivity of TES
Heigh_Tes7703   ! 5: m, storage height
TIni_Tes7703   ! 6: oC, initial temperature
nCvMax_Tes7703  ! 7: -, minimum relative plug height
nCvMin_Tes7703  ! 8: -, maximum relative plug height
maxTDiff_Tes7703  ! 9: K, maximum temperature difference between plugs
readMode_Tes7703  ! 10: 1: from table, 0: Tini and CapTot
Tref_Tes7703     ! 11: oC, reference temperature
UaBot_Tes7703 ! W/k 
Uaz1_Tes7703  ! W/k
Uaz2_Tes7703  ! W/k
Uaz3_Tes7703  ! W/k
UaTop_Tes7703 ! W/k
tMax_Tes7703
0	0	0 ! 17-20 unsused parameters
zInDp1_Tes7703 zOutDp1_Tes7703 zero Dp1Strat_Tes7703 ! 21 - 25: zIn, zOut, cp, strat
zInDp2_Tes7703 zOutDp2_Tes7703 zero Dp2Strat_Tes7703 ! 26 - 30: zIn, zOut, cp, strat
zInDp3_Tes7703 zOutDp3_Tes7703 zero Dp3Strat_Tes7703 ! 31 - 35: zIn, zOut, cp, strat
-1 -1 zero zero ! 36 - 40: zIn, zOut, cp, strat
-1 -1 zero zero ! 41 - 45: zIn, zOut, cp, strat
-1 -1 zero zero ! 46 - 50: zIn, zOut, cp, strat
-1 -1 zero zero ! 51 - 55: zIn, zOut, cp, strat
-1 -1 zero zero ! 56 - 60: zIn, zOut, cp, strat
-1 -1 zero zero ! 61 - 65: zIn, zOut, cp, strat
-1 -1 zero zero ! 66 - 70: zIn, zOut, cp, strat
zSen1_Tes7703 zSen2_Tes7703 zSen3_Tes7703 zSen4_Tes7703 zSen5_Tes7703 zSen6_Tes7703 zSen7_Tes7703 zSen8_Tes7703 zSen9_Tes7703 zSen10_Tes7703 ! 61-71 : relative storage temperature sensor heights 
zSenAvgBot1_Tes7703 zSenAvgTop1_Tes7703 ! 71-72 : relative position of lower and upper edge temeprature sensors
zSenAvgBot2_Tes7703 zSenAvgTop2_Tes7703 ! 73-74 : relative position of lower and upper edge temeprature sensors
zSenAvgBot3_Tes7703 zSenAvgTop3_Tes7703 ! 75-76 : relative position of lower and upper edge temeprature sensors
zSenAvgBot4_Tes7703 zSenAvgTop4_Tes7703 ! 77-78 : relative position of lower and upper edge temeprature sensors
zSenAvgBot5_Tes7703 zSenAvgTop5_Tes7703 ! 79-80 : relative position of lower and upper edge temeprature sensors
MoInsPlate_Tes7703 ! 81: 0-2, Insulation Plate Mode: 0 = no insulation plate inside TES, 1 = insulation plate at fixed relative height, 2 = insulation plate at fixed temperature / density controlled 
zInsPlate_Tes7703  ! 82: 0-1, relative position of fixed height insulation plate inside TES (only for Insulation Plate Mode = 1
TinsPlate_Tes7703  ! 83: oC, temperature at which moveable insulation plate floats in TES (only for Insulation Plate Mode = 2)
UAinsPlate_Tes7703 ! 84: W/K, overall heat transfer coefficient across moveable insulation plate (including heat transfer in gap between plate and wall and in wall at the respective height)
nHxUsed_Tes7703     ! 85: number Of used Hx
** Parameters for heat Exchanger number 1
zInHx1_Tes7703 zOutHx1_Tes7703 dInHx1_Tes7703 dOutHx1_Tes7703 LHx1_Tes7703 LamHx1_Tes7703 brineConcHx1_Tes7703 VHx1_Tes7703 CpHx1_Tes7703 RhoHx1_Tes7703 nCvHx1_Tes7703 modHx1_Tes7703 nNuHx1_Tes7703 cNuHx1_Tes7703 dUaMfrHx1_Tes7703 dUadTHx1_Tes7703 dUaTHx1_Tes7703 UaHx1_Tes7703 startUpHx1_Tes7703 ! Heax exchanger 1
** Parameters for heat Exchanger number 2
-1 -1 zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero ! Heax exchanger 2
** Parameters for heat Exchanger number 3
-1 -1 zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero ! Heax exchanger 3
** Parameters for heat Exchanger number 4
-1 -1 zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero ! Heax exchanger 4
** Parameters for heat Exchanger number 5
-1 -1 zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero ! Heax exchanger 5
** Parameters for heat Exchanger number 6
-1 -1 zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero ! Heax exchanger 6
** 20 height position for any heat source, e.g. electrical backup or heat pump condenser. Any position can be due to a different heat source
zAux1_Tes7703 zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero 
INPUTS 69
************10 DIRECT PORTS INPUTS***************
Tdp1In_Tes7703 Mfrdp1_Tes7703 Tdp1InRev_Tes7703
Tdp2In_Tes7703 Mfrdp2_Tes7703 Tdp2InRev_Tes7703
Tdp3In_Tes7703 Mfrdp3_Tes7703 Tdp3InRev_Tes7703
zero zero zero
zero zero zero
zero zero zero
zero zero zero
zero zero zero
zero zero zero
zero zero zero
****************
TroomStore
***************** 6 HX INPUTS ******************
Thx1In_Tes7703 Mfrhx1_Tes7703 Thx1InRev_Tes7703
zero zero zero
zero zero zero
zero zero zero
zero zero zero
zero zero zero
***************** 20 HEAT SOURCE INPUTS ******************
qAux1_Tes7703 zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero zero 
****************** INTIAL INPUTS***********************
zero zero zero zero zero zero zero zero zero zero 
zero zero zero zero zero zero zero zero zero zero 
zero zero zero zero zero zero zero zero zero zero 
zero zero zero zero zero zero zero zero zero zero 
zero zero zero zero zero zero zero zero zero zero 
zero zero zero zero zero zero zero zero zero zero 
zero zero zero zero zero zero zero zero zero 
*****************OUTPUTS****************
EQUATIONS 3
Qdp1_Tes7703=[50,31] ! 
Qdp2_Tes7703=[50,32] ! 
Qdp3_Tes7703=[50,33] ! 
EQUATIONS 21
TAvg_Tes7703 = [50,180] ! Average storage temperature 
***Temperatures at 10 equallay distributed height 
T1_Tes7703 =[50,21] !temperature at 0.05 
T2_Tes7703 =[50,22] !temperature at 0.15 
T3_Tes7703 =[50,23] !temperature at 0.25 
T4_Tes7703 =[50,24] !temperature at 0.35 
T5_Tes7703 =[50,25] !temperature at 0.45 
T6_Tes7703 =[50,26] !temperature at 0.55 
T7_Tes7703 =[50,27] !temperature at 0.65 
T8_Tes7703 =[50,28] !temperature at 0.75 
T9_Tes7703 =[50,29] !temperature at 0.85 
T10_Tes7703 =[50,30] !temperature at 0.95 
***Temperatures at 10 sensors user defined height
Tsen1_Tes7703 =[50,71] ! temperature at user defined sensor height Tsen1_Tes7703 
Tsen2_Tes7703 =[50,72] ! temperature at user defined sensor height Tsen2_Tes7703 
Tsen3_Tes7703 =[50,73] ! temperature at user defined sensor height Tsen3_Tes7703 
Tsen4_Tes7703 =[50,74] ! temperature at user defined sensor height Tsen4_Tes7703 
Tsen5_Tes7703 =[50,75] ! temperature at user defined sensor height Tsen5_Tes7703 
Tsen6_Tes7703 =[50,76] ! temperature at user defined sensor height Tsen6_Tes7703 
Tsen7_Tes7703 =[50,77] ! temperature at user defined sensor height Tsen7_Tes7703 
Tsen8_Tes7703 =[50,78] ! temperature at user defined sensor height Tsen8_Tes7703 
Tsen9_Tes7703 =[50,79] ! temperature at user defined sensor height Tsen9_Tes7703 
Tsen10_Tes7703 =[50,80] ! temperature at user defined sensor height Tsen10_Tes7703 
EQUATIONS 1
Qhx1Out_Tes7703=[50,104] ! 
EQUATIONS 1
qHeatSource_Tes7703 = [50,181] ! Heat input of all auxiliary heat sources [kW]
EQUATIONS 5
sumQv_Tes7703     = [50,176] ! Heat input of all heat exchangers [kW]
sumQLoss_Tes7703  = [50,177] ! Heat Losses of the Tes [kW]
sumQAcum_Tes7703  = [50,178] ! Sensible accumulated heat [kW]
sumQPorts_Tes7703 = [50,179] ! Heat Input by direct ports [kW]
Imb_Tes7703       = [50,64]  ! Heat Imbalance in Tes  IMB = sumQv - sumQLoss -sumQAcum + sumQPort
CONSTANTS 1 
unitPrinter_Tes7703 = 51 
ASSIGN temp\TES7703_MO.Prt unitPrinter_Tes7703
UNIT 51 TYPE 46
PARAMETERS 5
unitPrinter_Tes7703 ! 1: Logical unit number, -
-1  ! 2: Logical unit for monthly summaries
1 ! 3: Relative or absolute start time. 0: print at time intervals relative to the simulation start time. 1: print at absolute time intervals. No effect for monthly integrations
-1  ! 4: Printing & integrating interval, h. -1 for monthly integration
0  ! 5: Number of inputs to avoid integration
INPUTS 10
sumQv_Tes1 sumQLoss_Tes1 sumQAcum_Tes1 sumQPorts_Tes1 Imb_Tes1 Qdp1_Tes7703 Qdp2_Tes7703 Qdp3_Tes7703 Qhx1Out_Tes7703 qHeatSource_Tes7703 
zero zero zero zero zero zero zero zero zero zero 
*************************************
********** Online Plotter ***********
*************************************

UNIT 501 TYPE 65     ! Online Plotter HX 
PARAMETERS 12   
10     ! 1 Nb. of left-axis variables 
0     ! 2 Nb. of right-axis variables
0     ! 3 Left axis minimum 
100     ! 4 Left axis maximum -
0     ! 5 Right axis minimum 
100     ! 6 Right axis maximum 
nPlotsPerSim     ! 7 Number of plots per simulation 
12     ! 8 X-axis gridpoints
1     ! 9 Shut off Online w/o removing 
-1     ! 10 Logical unit for output file 
0     ! 11 Output file units
0     ! 12 Output file delimiter
INPUTS 10     
T1_Tes7703 T2_Tes7703 T3_Tes7703 T4_Tes7703 T5_Tes7703 T6_Tes7703 T7_Tes7703 T8_Tes7703 T9_Tes7703 T10_Tes7703 
T1_Tes7703 T2_Tes7703 T3_Tes7703 T4_Tes7703 T5_Tes7703 T6_Tes7703 T7_Tes7703 T8_Tes7703 T9_Tes7703 T10_Tes7703 
LABELS  3         
Temperatures  
MassFlows  
Tes%d 


"""

        assert actualDdckContent == expectedDdckContent

    @staticmethod
    def _setupExternalConnectionMocks(storageTank):
        for i, heatExchanger in enumerate(storageTank.heatExchangers):
            externalFromPortConnection = _StrictMock(displayName=f"hx{i}ExtFromPortConn")
            heatExchanger.port1.connectionList.append(externalFromPortConnection)

            externalToPortConnection = _StrictMock(displayName=f"hx{i}ExtToPortConn")
            heatExchanger.port2.connectionList.append(externalToPortConnection)

        for i, directPortPair in enumerate(storageTank.directPortPairs):
            externalFromPortConnection = _StrictMock(
                displayName=f"dpp{i}ExtFromPortConn",
                fromPort=_StrictMock(),
                toPort=directPortPair.fromPort,
            )
            directPortPair.fromPort.connectionList.append(
                externalFromPortConnection
            )

            externalToPortConnection = _StrictMock(
                displayName=f"dpp{i}ExtToPortConn",
                fromPort=directPortPair.toPort,
                toPort=_StrictMock(),
            )
            directPortPair.toPort.connectionList.append(
                externalToPortConnection
            )

    @staticmethod
    def _createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, projectPath):
        application = _widgets.QApplication([])

        mainWindow = _widgets.QMainWindow()

        editorMock = _widgets.QWidget(parent=mainWindow)
        editorMock.connectionList = []
        editorMock.logger = logger
        editorMock.trnsysObj = []
        editorMock.groupList = []
        editorMock.projectPath = str(projectPath)
        editorMock.splitter = _mock.Mock(name="splitter")
        editorMock.idGen = _mock.Mock(
            name="idGen",
            spec_set=[
                "getID",
                "getTrnsysID",
                "getStoragenTes",
                "getStorageType",
                "getConnID",
            ],
        )
        editorMock.moveDirectPorts = True
        editorMock.editorMode = 1
        editorMock.snapGrid = False
        editorMock.alignMode = False

        editorMock.idGen.getID = lambda: 7701
        editorMock.idGen.getTrnsysID = lambda: 7702
        editorMock.idGen.getStoragenTes = lambda: 7703
        editorMock.idGen.getStorageType = lambda: 7704
        editorMock.idGen.getConnID = lambda: 7705

        graphicsScene = _widgets.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = graphicsScene

        diagramViewMock = _widgets.QGraphicsView(graphicsScene, parent=editorMock)
        diagramViewMock.logger = logger

        mainWindow.setCentralWidget(editorMock)
        mainWindow.showMinimized()

        return diagramViewMock, [application, mainWindow, editorMock, graphicsScene]
