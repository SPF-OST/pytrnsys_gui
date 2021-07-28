# pylint: skip-file
# type: ignore

import os
import numpy as num


class Type1924_TesPlugFlow:
    def __init__(self):

        self.listParHx = ["", "", "", ""]
        self.listParPort = num.zeros(10)
        self.listParUa = num.zeros(10)

        self.nMaxPorts = 10
        self.nMaxHx = 6
        self.nMaxSensor = 10
        self.nMaxAvgSensor = 5

        self.sLine = "*************************************\n"
        self.extension = "ddck"

        self.setDefault()

    def setInputs(self, inputs, connectorsPort, connectorsHx, connectorsAux):

        self.inputs = inputs
        self.connectorsPort = connectorsPort
        self.connectorsHx = connectorsHx
        self.connectorsAux = connectorsAux

    def setDefault(self):
        self.Ua = [1, 1, 1, 1, 1]

    def getOneHxInputs(self, nTes, idHx, connectorHx):

        lines = ""

        line = "EQUATIONS 3\n"
        lines = lines + line
        line = "Thx%dIn_Tes%d = %s ! @connectDdck\n" % (idHx, nTes, connectorHx[idHx - 1]["T"])
        lines = lines + line
        line = "Mfrhx%d_Tes%d = %s ! @connectDdck\n" % (idHx, nTes, connectorHx[idHx - 1]["Mfr"])
        lines = lines + line
        line = "Thx%dInRev_Tes%d = %s ! @connectDdck\n" % (idHx, nTes, connectorHx[idHx - 1]["Trev"])
        lines = lines + line

        return lines

    @staticmethod
    def _getOnePortInputs(nTes, idPort, connectorPort):

        lines = ""

        line = "EQUATIONS 3\n"
        lines = lines + line
        line = "Tdp%dIn_Tes%d = %s ! @connectDdck\n" % (idPort, nTes, connectorPort[idPort - 1]["T"])
        lines = lines + line
        line = "Mfrdp%d_Tes%d = %s ! @connectDdck\n" % (idPort, nTes, connectorPort[idPort - 1]["Mfr"])
        lines = lines + line
        line = "Tdp%dInRev_Tes%d = %s ! @connectDdck\n" % (idPort, nTes, connectorPort[idPort - 1]["Trev"])
        lines = lines + line

        return lines

    def getOnePortParConn(self, idPort, nTes, connectorPort):

        lines = "*********Connecting values of DIRECT PORT=%d***********\n" % (idPort + 1)

        line = "CONSTANTS 2\n"
        lines = lines + line

        line = "zInDp%d_Tes%d=%.2f ! @connectDdck \n" % (idPort + 1, nTes, connectorPort[idPort]["zIn"])
        lines = lines + line
        line = "zOutDp%d_Tes%d=%.2f ! @connectDdck \n" % (idPort + 1, nTes, connectorPort[idPort]["zOut"])
        lines = lines + line

        return lines

    def getOnePortPar(self, idPort, nTes):

        lines = "*********Constant of DIRECT PORT=%d***********\n" % (idPort + 1)

        line = "CONSTANTS 1\n"
        lines = lines + line
        line = "Dp%dStrat_Tes%d=0 ! 0: no forced stratification ; 1: force to stratify\n" % (idPort + 1, nTes)
        lines = lines + line

        return lines

    def getSensorPositionValues(self, nTes):

        lines = self.sLine + "** USER DEFINED TEMPERATURE SENSOR HEIGHTS. To be changed by user \n" + self.sLine

        line = "CONSTANTS 10\n"
        lines = lines + line

        z = 0.05
        for i in range(10):
            line = "zSen%d_Tes%d=%.2f\n" % (i + 1, nTes, z)
            lines = lines + line
            z = z + 0.1

        return lines

    def getOneHxParConnValues(self, nTes, idHx, connectHx):

        lines = "*********Connecting values of HX=%d***********\n" % idHx

        line = "CONSTANTS 4\n"
        lines = lines + line

        line = "zInhx%d_Tes%d=%.2f  ! @connectDdck\n" % (idHx, nTes, connectHx[idHx - 1]["zIn"])
        lines = lines + line
        line = "zOuthx%d_Tes%d=%.2f ! @connectDdck\n" % (idHx, nTes, connectHx[idHx - 1]["zOut"])
        lines = lines + line
        line = "Cphx%d_Tes%d=%s     ! @connectDdck\n" % (idHx, nTes, connectHx[idHx - 1]["cp"])
        lines = lines + line
        line = "Rhohx%d_Tes%d=%s    ! @connectDdck\n" % (idHx, nTes, connectHx[idHx - 1]["rho"])
        lines = lines + line

        return lines

    def getOneHxParValues(self, nTes, idHx):

        lines = "*********Constant values of HX=%d***********\n" % idHx

        line = "CONSTANTS 15\n"
        lines = lines + line

        line = "dInHx%d_Tes%d=0.05 ! m only if modHx%d=1\n" % (idHx, nTes, idHx)
        lines = lines + line
        line = "dOutHx%d_Tes%d=0.06 ! m only if modHx%d=1\n" % (idHx, nTes, idHx)
        lines = lines + line

        line = "LHx%d_Tes%d=20 ! m only if modHx%d=1\n" % (idHx, nTes, idHx)
        lines = lines + line
        line = "LamHx%d_Tes%d=50 ! W/mK only if modHx%d=1\n" % (idHx, nTes, idHx)
        lines = lines + line
        line = "brineConcHx%d_Tes%d=30 ! [0-100] only if modHx%d=1\n" % (idHx, nTes, idHx)
        lines = lines + line

        line = "VHx%d_Tes%d=0. \n" % (idHx, nTes)
        lines = lines + line
        line = "nCvHx%d_Tes%d=20 \n" % (idHx, nTes)
        lines = lines + line

        line = "modHx%d_Tes%d=1 ! modHX1, 0 = physical model, 1 = Drueck-model (Multiport)\n" % (idHx, nTes)
        lines = lines + line
        line = "nNuHx%d_Tes%d=0.5 !  only if modHx%d=1\n" % (idHx, nTes, idHx)
        lines = lines + line
        line = "cNuHx%d_Tes%d=0.25 !  only if modHx%d=1\n" % (idHx, nTes, idHx)
        lines = lines + line

        line = "dUaMfrHx%d_Tes%d=0.375 ! only if modHx%d=0\n" % (idHx, nTes, idHx)
        lines = lines + line
        line = "dUadTHx%d_Tes%d=0.0 ! only if modHx%d=0\n" % (idHx, nTes, idHx)
        lines = lines + line
        line = "dUaTHx%d_Tes%d=0.458 ! only if modHx%d=0\n" % (idHx, nTes, idHx)
        lines = lines + line
        line = "UaHx%d_Tes%d=1105*ratioTes%d ! kJ/hK only if modHx%d=0\n" % (idHx, nTes, nTes, idHx)
        lines = lines + line

        line = "startUpHx%d_Tes%d=0. ! only if modHx%d=0\n" % (idHx, nTes, idHx)
        lines = lines + line

        return lines

    def getHxParValues(self, nTes, nHx):

        lines = ""
        for i in range(self.nMaxHx):
            idHx = i + 1
            line = "** Parameters for heat Exchanger number %d\n" % idHx
            lines = lines + line
            if idHx <= nHx:
                line = "zInHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "zOutHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "dInHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "dOutHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "LHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "LamHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "brineConcHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "VHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "CpHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "RhoHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "nCvHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "modHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "nNuHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "cNuHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "dUaMfrHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "dUadTHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "dUaTHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "UaHx%d_Tes%d " % (idHx, nTes)
                lines = lines + line
                line = "startUpHx%d_Tes%d ! Heax exchanger %d\n" % (idHx, nTes, idHx)
                lines = lines + line
            else:
                line = "-1 -1 "
                lines = lines + line  # zin and zout = -1 when not used
                for i in range(17):
                    line = "zero "
                    lines = lines + line
                lines = lines + "! Heax exchanger %d\n" % (idHx)

        return lines

    def getUaPar(self, nTes):

        lines = ""

        line = "UaBot_Tes%d ! W/k \n" % (nTes)
        lines = lines + line
        line = "Uaz1_Tes%d  ! W/k\n" % (nTes)
        lines = lines + line
        line = "Uaz2_Tes%d  ! W/k\n" % (nTes)
        lines = lines + line
        line = "Uaz3_Tes%d  ! W/k\n" % (nTes)
        lines = lines + line
        line = "UaTop_Tes%d ! W/k\n" % (nTes)
        lines = lines + line

        return lines

    def getUaParValues(self, nTes, Ua):

        lines = ""
        myList = []
        line = "CONSTANTS 10\n"
        lines = lines + line

        line = "Ufoam_Tes%d= 0.67 ! W/(m2K) 6 cm of foam of 0.04 W/(mK) \n" % (nTes)
        lines = lines + line
        line = "Ubot_Tes%d = 1.5 ! W/(m2K) 2 cm of foam of 0.04 W/(mK)\n" % (nTes)
        lines = lines + line
        line = "Atop_Tes%d = Vol_Tes%d/Heigh_Tes%d ! m2\n" % (nTes, nTes, nTes)
        lines = lines + line
        line = "Diameter_Tes%d = (4*ATop_Tes%d/PI)^0.5 ! m \n" % (nTes, nTes)
        lines = lines + line
        line = "ALat_Tes%d = Heigh_Tes%d*PI*Diameter_Tes%d ! m2\n" % (nTes, nTes, nTes)
        lines = lines + line

        line = "UaBot_Tes%d= Ubot_Tes%d*ATop_Tes%d ! @userDefined W/k \n" % (nTes, nTes, nTes)
        lines = lines + line
        line = "Uaz1_Tes%d = Ufoam_Tes%d*ALat_Tes%d/3 ! @userDefined W/k\n" % (nTes, nTes, nTes)
        lines = lines + line
        line = "Uaz2_Tes%d = Ufoam_Tes%d*ALat_Tes%d/3 ! @userDefined W/k\n" % (nTes, nTes, nTes)
        lines = lines + line
        line = "Uaz3_Tes%d = Ufoam_Tes%d*ALat_Tes%d/3 ! @userDefined W/k\n" % (nTes, nTes, nTes)
        lines = lines + line
        line = "UaTop_Tes%d = Ufoam_Tes%d*ATop_Tes%d ! @userDefined W/k\n" % (nTes, nTes, nTes)
        lines = lines + line

        return lines

    def getFirst12Par(self, nTes):

        lines = ""
        line = "Vol_Tes%d     ! 1: m3, volume of store\n" % nTes
        lines = lines + line
        line = "RhoWat_Tes%d  ! 2: kg/m3, density of storage media\n" % nTes
        lines = lines + line
        line = "CpWat_Tes%d   ! 3: kJ/kgK, specific heat of storage media\n" % nTes
        lines = lines + line
        line = "lamZ_Tes%d    ! 4: W/mK, effective vertical thermal conductivity of TES\n" % nTes
        lines = lines + line
        line = "Heigh_Tes%d   ! 5: m, storage height\n" % nTes
        lines = lines + line
        line = "TIni_Tes%d   ! 6: oC, initial temperature\n" % nTes
        lines = lines + line
        line = "nCvMax_Tes%d  ! 7: -, minimum relative plug height\n" % nTes
        lines = lines + line
        line = "nCvMin_Tes%d  ! 8: -, maximum relative plug height\n" % nTes
        lines = lines + line
        line = "maxTDiff_Tes%d  ! 9: K, maximum temperature difference between plugs\n" % nTes
        lines = lines + line
        line = "readMode_Tes%d  ! 10: 1: from table, 0: Tini and CapTot\n" % nTes
        lines = lines + line
        line = "Tref_Tes%d     ! 11: oC, reference temperature\n" % nTes
        lines = lines + line

        return lines

    def getFirst12ParVar(self, nTes):

        lines = "CONSTANTS 12\n"
        line = "Vol_Tes%d=1          ! 1: m3, volume of store\n" % nTes
        lines = lines + line
        line = "RhoWat_Tes%d=RhoWat  ! 2: kg/m3, density of storage media\n" % nTes
        lines = lines + line
        line = "CpWat_Tes%d=CpWat    ! 3: kJ/kgK, specific heat of storage media\n" % nTes
        lines = lines + line
        line = "lamZ_Tes%d=0.6       ! 4: W/mK, effective vertical thermal conductivity of TES\n" % nTes
        lines = lines + line
        line = "Heigh_Tes%d=1.       ! 5: m, storage height\n" % nTes
        lines = lines + line
        line = "Tini_Tes%d=60.       ! 6: oC, initial temperature\n" % nTes
        lines = lines + line
        line = "nCvMax_Tes%d=400     ! 7: -, minimum relative plug height\n" % nTes
        lines = lines + line
        line = "nCvMin_Tes%d=20      ! 8: -, maximum relative plug height\n" % nTes
        lines = lines + line
        line = "maxTDiff_Tes%d=0.015 ! 9: K, maximum temperature difference between plugs\n" % nTes
        lines = lines + line
        line = "readMode_Tes%d=0     ! 10: 1: from table, 0: Tini and CapTot\n" % nTes
        lines = lines + line
        line = "Tref_Tes%d=273.15    ! 11: oC, reference temperature\n" % nTes
        lines = lines + line
        line = "Tmax_Tes%d=100.       ! 6: oC, initial temperature\n" % nTes
        lines = lines + line

        line = self.getUaParValues(nTes, self.Ua)
        lines = lines + line

        return lines

    def getHeighDirectPortsPar(self, nPorts, nTes):

        lines = ""
        parId = 21
        for i in range(self.nMaxPorts):
            if i <= nPorts - 1:
                line = "zInDp%d_Tes%d zOutDp%d_Tes%d zero Dp%dStrat_Tes%d ! %d - %d: zIn, zOut, cp, strat\n" % (
                    i + 1,
                    nTes,
                    i + 1,
                    nTes,
                    i + 1,
                    nTes,
                    parId,
                    parId + 4,
                )
                lines = lines + line
            else:
                line = "-1 -1 zero zero ! %d - %d: zIn, zOut, cp, strat\n" % (parId, parId + 4)
                lines = lines + line

            parId = parId + 5

        return lines

    def getHeighSensorPar(self, nTes):

        lines = ""
        parId = 61
        for i in range(self.nMaxSensor):
            line = "zSen%d_Tes%d " % (i + 1, nTes)
            lines = lines + line

        line = "! %d-%d : relative storage temperature sensor heights \n" % (parId, parId + 10)
        lines = lines + line

        return lines

    def getHeatSourcesValues(self, nTes, nHeatSources, connectorAux):

        lines = ""
        line = self.sLine + "************ AUXILIAR HEATING**********\n"
        if nHeatSources > 0:
            line = "CONSTANTS %d\n" % (nHeatSources * 2)
            lines = lines + line

            for i in range(nHeatSources):
                line = "zAux%d_Tes%d=%.2f !connectDDck\n" % (i + 1, nTes, connectorAux[i]["zAux"])
                lines = lines + line
                line = "qAux%d_Tes%d=%.2f !connectDDck\n" % (i + 1, nTes, connectorAux[i]["qAux"])
                lines = lines + line

            line = "\n"
            lines = lines + line

        return lines

    def getPositionOfHeatSources(self, nTes, nHeatSources):

        lines = ""
        line = "** 20 height position for any heat source, e.g. electrical backup or heat pump condenser. Any position can be due to a different heat source\n"
        lines = lines + line
        for i in range(20):
            if i <= nHeatSources - 1:
                line = "zAux%d_Tes%d " % (i + 1, nTes)
                lines = lines + line
            else:
                line = "zero "
                lines = lines + line

        line = "\n"
        lines = lines + line

        return lines

    def getHeighAvgSensorParValues(self, nTes):

        lines = self.sLine + "** USER DEFINED AVERAGED TEMPERATURE SENSOR HEIGHTS. To be changed by user \n" + self.sLine

        line = "CONSTANTS 10\n"
        lines = lines + line
        z = 0.05
        for i in range(self.nMaxAvgSensor):
            line = "zSenAvgBot%d_Tes%d = %.2f\n" % (i + 1, nTes, z)
            lines = lines + line
            line = "zSenAvgTop%d_Tes%d = %.2f\n" % (i + 1, nTes, z + 0.1)
            lines = lines + line
            z = z + 0.2

        return lines

    def getHeighAvgSensorPar(self, nTes):

        lines = ""
        parId = 71
        for i in range(self.nMaxAvgSensor):
            line = (
                "zSenAvgBot%d_Tes%d zSenAvgTop%d_Tes%d ! %d-%d : relative position of lower and upper edge temeprature sensors\n"
                % (i + 1, nTes, i + 1, nTes, parId, parId + 1)
            )
            lines = lines + line
            parId = parId + 2

        return lines

    def getInsulationPlateParValues(self, nTes):

        lines = "************* MOVING PLATE *******************\n"

        lines = lines + "CONSTANTS 4\n"

        line = (
            "MoInsPlate_Tes%d=0 ! 0-2, Insulation Plate Mode: 0 = no insulation plate inside TES, 1 = insulation plate at fixed relative height, 2 = insulation plate at fixed temperature / density controlled \n"
            % nTes
        )
        lines = lines + line
        line = (
            "zInsPlate_Tes%d=0  ! 0-1, relative position of fixed height insulation plate inside TES (only for Insulation Plate Mode = 1\n"
            % nTes
        )
        lines = lines + line
        line = (
            "TinsPlate_Tes%d=0  ! oC, temperature at which moveable insulation plate floats in TES (only for Insulation Plate Mode = 2)\n"
            % nTes
        )
        lines = lines + line
        line = (
            "UAinsPlate_Tes%d=0 ! W/K, overall heat transfer coefficient across moveable insulation plate (including heat transfer in gap between plate and wall and in wall at the respective height)\n"
            % nTes
        )
        lines = lines + line

        return lines

    def getInsulationPlatePar(self, nTes):

        lines = ""
        line = (
            "MoInsPlate_Tes%d ! 81: 0-2, Insulation Plate Mode: 0 = no insulation plate inside TES, 1 = insulation plate at fixed relative height, 2 = insulation plate at fixed temperature / density controlled \n"
            % nTes
        )
        lines = lines + line
        line = (
            "zInsPlate_Tes%d  ! 82: 0-1, relative position of fixed height insulation plate inside TES (only for Insulation Plate Mode = 1\n"
            % nTes
        )
        lines = lines + line
        line = (
            "TinsPlate_Tes%d  ! 83: oC, temperature at which moveable insulation plate floats in TES (only for Insulation Plate Mode = 2)\n"
            % nTes
        )
        lines = lines + line
        line = (
            "UAinsPlate_Tes%d ! 84: W/K, overall heat transfer coefficient across moveable insulation plate (including heat transfer in gap between plate and wall and in wall at the respective height)\n"
            % nTes
        )
        lines = lines + line

        return lines

    def getInputs(self, inputs):

        nInputs = 69
        nHx = inputs["nHx"]
        nTes = inputs["nTes"]
        nPorts = inputs["nPorts"]
        nHeatSources = inputs["nHeatSources"]

        lines = ""
        line = "INPUTS %d\n" % nInputs
        lines = lines + line
        line = "************10 DIRECT PORTS INPUTS***************\n"
        lines = lines + line

        for idPort in range(self.nMaxPorts):  # This adds 30 inputs
            if idPort <= nPorts - 1:
                line = "Tdp%dIn_Tes%d Mfrdp%d_Tes%d Tdp%dInRev_Tes%d\n" % (
                    idPort + 1,
                    nTes,
                    idPort + 1,
                    nTes,
                    idPort + 1,
                    nTes,
                )

            else:
                line = "zero zero zero\n"
            lines = lines + line
        lines = lines + "****************\nTroomStore"  # This adds one input
        lines = lines + "\n***************** 6 HX INPUTS ******************\n"

        for idHx in range(self.nMaxHx):  # This adds 18 inputs
            if idHx <= nHx - 1:
                line = "Thx%dIn_Tes%d Mfrhx%d_Tes%d Thx%dInRev_Tes%d\n" % (
                    idHx + 1,
                    nTes,
                    idHx + 1,
                    nTes,
                    idHx + 1,
                    nTes,
                )
            else:
                line = "zero zero zero\n"
            lines = lines + line
        lines = lines + "***************** 20 HEAT SOURCE INPUTS ******************\n"

        for i in range(20):  # This adds 20 inputs
            if i <= nHeatSources - 1:
                line = "qAux%d_Tes%d " % (i + 1, nTes)
            else:
                line = "zero "
            lines = lines + line
        lines = lines + "\n"

        lines = lines + "****************** INTIAL INPUTS***********************\n"

        for i in range(69):
            line = "zero "
            lines = lines + line
            if i == 9 or i == 19 or i == 29 or i == 39 or i == 49 or i == 59 or i == 69:
                line = "\n"
                lines = lines + line

        line = "\n"
        lines = lines + line

        return lines

    def getOutputs(self, inputs):

        nUnit = inputs["nUnit"]
        nTes = inputs["nTes"]
        nHx = inputs["nHx"]
        nPorts = inputs["nPorts"]

        lines = "*****************OUTPUTS****************\n"

        nEq = nPorts
        line = "EQUATIONS %d\n" % nEq
        lines = lines + line

        for idPort in range(nPorts):
            line = "Qdp%d_Tes%d=[%d,%d] ! \n" % (idPort + 1, nTes, nUnit, 30 + idPort + 1)
            lines = lines + line

        nEq = 21
        line = "EQUATIONS %d\n" % nEq
        lines = lines + line

        line = "TAvg_Tes%d = [%d,180] ! Average storage temperature \n" % (nTes, nUnit)
        lines = lines + line
        line = "***Temperatures at 10 equallay distributed height \n"
        lines = lines + line
        counter = 21
        for i in range(10):
            height = 0.05 + 0.1 * i
            line = "T%d_Tes%d =[%d,%d] !temperature at %.2f \n" % (i + 1, nTes, nUnit, counter, height)
            lines = lines + line
            counter = counter + 1

        line = "***Temperatures at 10 sensors user defined height\n"
        lines = lines + line
        counter = 71
        for i in range(10):
            line = "Tsen%d_Tes%d =[%d,%d] ! temperature at user defined sensor height Tsen%d_Tes%d \n" % (
                i + 1,
                nTes,
                nUnit,
                counter,
                i + 1,
                nTes,
            )
            lines = lines + line
            counter = counter + 1

        nEq = nHx
        if nEq > 0:
            line = "EQUATIONS %d\n" % nEq
            lines = lines + line

        counter = 102
        for idHx in range(nHx):
            line = "Qhx%dOut_Tes%d=[%d,%d] ! \n" % (idHx + 1, nTes, nUnit, counter + 2)
            lines = lines + line
            counter = counter + 10

        line = "EQUATIONS 1\n"
        lines = lines + line

        line = "qHeatSource_Tes%d = [%d,181] ! Heat input of all auxiliary heat sources [kW]\n" % (nTes, nUnit)
        lines = lines + line

        line = "EQUATIONS 5\n"
        lines = lines + line

        line = "sumQv_Tes%d     = [%d,176] ! Heat input of all heat exchangers [kW]\n" % (nTes, nUnit)
        lines = lines + line
        line = "sumQLoss_Tes%d  = [%d,177] ! Heat Losses of the Tes [kW]\n" % (nTes, nUnit)
        lines = lines + line
        line = "sumQAcum_Tes%d  = [%d,178] ! Sensible accumulated heat [kW]\n" % (nTes, nUnit)
        lines = lines + line
        line = "sumQPorts_Tes%d = [%d,179] ! Heat Input by direct ports [kW]\n" % (nTes, nUnit)
        lines = lines + line
        line = "Imb_Tes%d       = [%d,64]  ! Heat Imbalance in Tes  IMB = sumQv - sumQLoss -sumQAcum + sumQPort\n" % (
            nTes,
            nUnit,
        )
        lines = lines + line

        return lines

    def getMonthyPrinter(self, nTes, nUnit, inputs):

        nPrinterUnit = nUnit + 1
        lines = ""
        line = "CONSTANTS 1 \n"
        lines = lines + line
        line = "unitPrinter_Tes%d = %d \n" % (nTes, nPrinterUnit)
        lines = lines + line
        line = "ASSIGN temp\TES%d_MO.Prt unitPrinter_Tes%d\n" % (nTes, nTes)
        lines = lines + line
        line = "UNIT %d TYPE 46\n" % nPrinterUnit
        lines = lines + line
        line = "PARAMETERS 5\n"
        lines = lines + line
        line = "unitPrinter_Tes%d ! 1: Logical unit number, -\n" % nTes
        lines = lines + line
        line = "-1  ! 2: Logical unit for monthly summaries\n"
        lines = lines + line
        line = "1 ! 3: Relative or absolute start time. 0: print at time intervals relative to the simulation start time. 1: print at absolute time intervals. No effect for monthly integrations\n"
        lines = lines + line
        line = "-1  ! 4: Printing & integrating interval, h. -1 for monthly integration\n"
        lines = lines + line
        line = "0  ! 5: Number of inputs to avoid integration\n"
        lines = lines + line
        # line = "0  ! 6: Number of inputs to avoid integration\n"; lines = lines + line
        nInputs = 5 + inputs["nPorts"] + inputs["nHx"] + 1  # +inputs["nHeatSources"]

        line = "INPUTS %d\n" % nInputs
        lines = lines + line
        line = "sumQv_Tes1 sumQLoss_Tes1 sumQAcum_Tes1 sumQPorts_Tes1 Imb_Tes1 "
        lines = lines + line
        for i in range(inputs["nPorts"]):
            line = "Qdp%d_Tes%d " % (i + 1, nTes)
            lines = lines + line

        for i in range(inputs["nHx"]):
            line = "Qhx%dOut_Tes%d " % (i + 1, nTes)
            lines = lines + line

        line = "qHeatSource_Tes%d " % (nTes)
        lines = lines + line

        lines = lines + "\n"

        for i in range(nInputs):
            line = "zero "
            lines = lines + line

        lines = lines + "\n"

        return lines

    def getOnlinePlotter(self, nTes, nUnit, inputs):

        nPrinterUnit = nUnit + 1
        lines = ""
        lines = lines + self.sLine
        line = "********** Online Plotter ***********\n"
        lines = lines + line
        lines = lines + self.sLine
        line = "\n"
        lines = lines + line
        line = "UNIT 501 TYPE 65     ! Online Plotter HX \n"
        lines = lines + line
        line = "PARAMETERS 12   \n"
        lines = lines + line
        line = "10     ! 1 Nb. of left-axis variables \n"
        lines = lines + line
        line = "0     ! 2 Nb. of right-axis variables\n"
        lines = lines + line
        line = "0     ! 3 Left axis minimum \n"
        lines = lines + line
        line = "100     ! 4 Left axis maximum -\n"
        lines = lines + line
        line = "0     ! 5 Right axis minimum \n"
        lines = lines + line
        line = "100     ! 6 Right axis maximum \n"
        lines = lines + line
        line = "nPlotsPerSim     ! 7 Number of plots per simulation \n"
        lines = lines + line
        line = "12     ! 8 X-axis gridpoints\n"
        lines = lines + line
        line = "1     ! 9 Shut off Online w/o removing \n"
        lines = lines + line
        line = "-1     ! 10 Logical unit for output file \n"
        lines = lines + line
        line = "0     ! 11 Output file units\n"
        lines = lines + line
        line = "0     ! 12 Output file delimiter\n"
        lines = lines + line
        line = "INPUTS 10     \n"
        lines = lines + line
        line = "T1_Tes%d T2_Tes%d T3_Tes%d T4_Tes%d T5_Tes%d T6_Tes%d T7_Tes%d T8_Tes%d T9_Tes%d T10_Tes%d \n" % (
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
        )
        lines = lines + line
        line = "T1_Tes%d T2_Tes%d T3_Tes%d T4_Tes%d T5_Tes%d T6_Tes%d T7_Tes%d T8_Tes%d T9_Tes%d T10_Tes%d \n" % (
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
            nTes,
        )
        lines = lines + line
        line = "LABELS  3         \n"
        lines = lines + line
        line = "Temperatures  \n"
        lines = lines + line
        line = "MassFlows  \n"
        lines = lines + line
        line = "Tes%d \n"
        lines = lines + line

        lines = lines + "\n"

        lines = lines + "\n"

        return lines

    def getParameters(self, inputs):

        nUnit = inputs["nUnit"]
        nType = inputs["nType"]
        nTes = inputs["nTes"]
        nPorts = inputs["nPorts"]
        nHx = inputs["nHx"]
        nHeatSources = inputs["nHeatSources"]

        lines = self.sLine + "********** TYPE DEFINITION **********\n" + self.sLine

        lines = lines + "UNIT %d TYPE %d     ! plug flow tank\n" % (nUnit, nType)
        lines = lines + "PARAMETERS 219 \n"
        lines = lines + self.getFirst12Par(nTes)
        lines = lines + self.getUaPar(nTes)
        lines = lines + "tMax_Tes%d\n" % nTes
        lines = lines + "0\t0\t0 ! 17-20 unsused parameters\n"
        lines = lines + self.getHeighDirectPortsPar(nPorts, nTes)
        lines = lines + self.getHeighSensorPar(nTes)
        lines = lines + self.getHeighAvgSensorPar(nTes)
        lines = lines + self.getInsulationPlatePar(nTes)
        lines = lines + "nHxUsed_Tes%d     ! 85: number Of used Hx\n" % nTes

        lines = lines + self.getHxParValues(nTes, nHx)
        lines = lines + self.getPositionOfHeatSources(nTes, nHeatSources)
        lines = lines + self.getInputs(inputs)
        lines = lines + self.getOutputs(inputs)
        lines = lines + self.getMonthyPrinter(nTes, nUnit, inputs)
        lines = lines + self.getOnlinePlotter(nTes, nUnit, inputs)
        return lines

    def getHead(self):

        header = open("C:\Daten\OngoingProject\SolTherm2050\Simulations\ddck\Generic\Head.ddck", "r")
        lines = header.read()
        header.close()

        return lines

    def createDDck(self, path, tankName, typeFile="ddck"):
        lines = ""
        if typeFile == "ddck":
            self.extension = "ddck"
            lines = lines + self.sLine
            lines = lines + ("**BEGIN %s.ddck\n" % tankName)
            lines = lines + self.sLine + "\n"
            lines = lines + self.sLine
            lines = lines + "** Plug-Flow Model exported from TRNSYS GUI\n"
            lines = lines + self.sLine + "\n"
            lines = lines + self.sLine
            lines = lines + "** To be checked: \n"
            lines = lines + "** check cp and rho values for the cirquits \n"
            lines = lines + "** default is cpwat and rhowat, for solarcirc usually cpbri and rhobri have to be used \n"
            lines = lines + self.sLine + "\n"
            lines = lines + self.sLine
            lines = lines + "** outputs to energy balance in kWh\n"
            lines = (
                lines + "** Following this naming standard : qSysIn_name, qSysOut_name, elSysIn_name, elSysOut_name\n"
            )
            lines = lines + self.sLine
            lines = lines + "EQUATIONS 3\n"
            lines = lines + ("qSysOut_Tes%sLoss = sumQLoss_Tes%d\n" % (tankName, self.inputs["nTes"]))
            lines = lines + ("qSysOut_Tes%sAcum = sumQAcum_Tes%d\n" % (tankName, self.inputs["nTes"]))
            lines = lines + ("elSysIn_Q_Tes%sAux = qHeatSource_Tes%d\n" % (tankName, self.inputs["nTes"]))

        elif typeFile == "dck":
            self.extension = "dck"
            lines = self.getHead()
        else:
            raise ValueError("typeFile %s unknown (Must be dck or ddck)")

        lines = lines + "\n" + self.sLine + "*** Inputs from hydraulic solver ****\n" + self.sLine

        nTes = self.inputs["nTes"]
        nHxs = self.inputs["nHx"]
        nPorts = self.inputs["nPorts"]
        nAux = self.inputs["nHeatSources"]
        nUnit = self.inputs["nUnit"]

        ddcxLines = ""

        for idPort in range(self.nMaxPorts):
            if idPort <= nPorts - 1:
                line = self._getOnePortInputs(nTes, idPort + 1, self.connectorsPort)
                lines = lines + line
                inputTemperature = line.split("\n")[1].split("=")[0].replace(" ", "")
                ddcxLine = (
                        "T"
                        + tankName
                        + "Port"
                        + self.connectorsPort[idPort]["side"]
                        + str(int(round(self.connectorsPort[idPort]["zIn"] * 100, 0)))
                        + "="
                        + inputTemperature
                        + "\n"
                )

                ddcxLines = ddcxLines + ddcxLine

        for idHx in range(self.nMaxHx):
            if idHx <= nHxs - 1:
                line = self.getOneHxInputs(nTes, idHx + 1, self.connectorsHx)
                lines = lines + line

        line = self.getHeatSourcesValues(nTes, nAux, self.connectorsAux)
        lines = lines + line

        lines = lines + self.sLine + "**** Outputs to hydraulic solver ****\n" + self.sLine

        nEq = nPorts
        if nEq > 0:
            line = "EQUATIONS %d\n" % nEq
            lines = lines + line
            line = "*** direct port outputs\n"
            lines = lines + line

        counter = 1
        for idPort in range(nPorts):
            outputTemperature = "Tdp%dOut_Tes%d" % (idPort + 1, nTes)
            line = outputTemperature + "=[%d,%d] ! \n" % (nUnit, counter)
            lines = lines + line
            ddcxLine = (
                    "T"
                    + tankName
                    + "Port"
                    + self.connectorsPort[idPort]["side"]
                    + str(int(self.connectorsPort[idPort]["zOut"] * 100))
                    + "="
                    + outputTemperature
                    + "\n"
            )
            ddcxLines = ddcxLines + ddcxLine
            counter = counter + 2

        nEq = nHxs
        if nEq > 0:
            line = "EQUATIONS %d\n" % nEq
            lines = lines + line
            line = "*** heat exchanger outputs\n"
            lines = lines + line

        counter = 102
        for idHx in range(nHxs):
            outputTemperature = "Thx%dOut_Tes%d" % (idHx + 1, nTes)
            line = outputTemperature + "=[%d,%d] ! \n" % (nUnit, counter)
            lines = lines + line
            ddcxLine = "T" + self.connectorsHx[idHx]["Name"] + "=" + outputTemperature + "\n"
            ddcxLines = ddcxLines + ddcxLine
            # line="Qhx%dOut_Tes%d=[%d,%d] ! \n"%(idHx+1,nTes,nUnit,counter+2);lines=lines+line
            counter = counter + 10

        if ddcxLines != "":
            header = self.sLine + "**BEGIN " + tankName + ".ddcx\n" + self.sLine
            header = header + "** This file is used to store the black box component outputs of " + tankName + "\n\n"
            ddcxLines = header + ddcxLines
            outfileDdcxPath = os.path.join(path, tankName)
            outfileDdcx = open(outfileDdcxPath + ".ddcx", "w")
            outfileDdcx.writelines(ddcxLines)
            outfileDdcx.close()

        lines = lines + "\n"

        line = self.sLine + "****** Parameters of Type1924 *******\n" + self.sLine
        lines = lines + line

        if nTes == 1:
            lines = lines + "CONSTANTS 3\n"
            line = "TRoomStore=15 ! @userDefined\n"
            lines = lines + line
            line = "VStoreRef = 0.763\n"
            lines = lines + line
        else:
            lines = lines + "CONSTANTS 1\n"
        line = "ratioTes%d = Vol_Tes%d / VStoreRef\n" % (nTes, nTes)
        lines = lines + line

        for idPort in range(self.nMaxPorts):
            if idPort <= nPorts - 1:

                line = self.getOnePortParConn(idPort, nTes, self.connectorsPort)
                lines = lines + line

        for idHx in range(self.nMaxHx):
            if idHx <= nHxs - 1:
                line = self.getOneHxParConnValues(nTes, idHx + 1, self.connectorsHx)
                lines = lines + line

        for idPort in range(self.nMaxPorts):
            if idPort <= nPorts - 1:

                line = self.getOnePortPar(idPort, nTes)
                lines = lines + line

        lines = lines + "********** HEAT EXCHANGER CONSTANTS*******\n"
        lines = lines + "CONSTANTS 1\n"
        lines = lines + "nHxUsed_Tes%d=%d \n" % (nTes, nHxs)

        for idHx in range(self.nMaxHx):
            if idHx <= nHxs - 1:
                line = self.getOneHxParValues(nTes, idHx + 1)
                lines = lines + line

        lines = lines + self.getSensorPositionValues(nTes)
        lines = lines + self.getHeighAvgSensorParValues(nTes)

        lines = lines + self.getFirst12ParVar(nTes)
        lines = lines + self.getInsulationPlateParValues(nTes)
        lines = lines + self.getParameters(self.inputs)

        nameWithPath = "%s\%s.%s" % (path, (tankName), self.extension)
        outfile = open(nameWithPath, "w")
        outfile.writelines(lines)
        outfile.close()
