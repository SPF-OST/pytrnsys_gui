# pylint: skip-file
# type: ignore

import os
import pathlib as _pl

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

    def setInputs(self, inputs, connectorsPort, connectorsHx, connectorsAux, nameTes):

        self.inputs = inputs
        self.connectorsPort = connectorsPort
        self.connectorsHx = connectorsHx
        self.connectorsAux = connectorsAux
        self.nameTes = nameTes

    def setDefault(self):
        self.Ua = [1, 1, 1, 1, 1]

    def getOneHxInputs(self, nTes, idHx, connectorHx):

        lines = ""

        line = "EQUATIONS 3\n"
        lines = lines + line
        line = "Thx%dIn = $%s\n" % (idHx, connectorHx[idHx - 1]["T"])
        lines = lines + line
        line = "Mfrhx%d = $%s\n" % (idHx, connectorHx[idHx - 1]["Mfr"])
        lines = lines + line
        line = "Thx%dInRev = $%s\n" % (idHx, connectorHx[idHx - 1]["Trev"])
        lines = lines + line

        return lines

    @staticmethod
    def _getOnePortInputs(nTes, idPort, connectorPort):

        #This should be replaced by nomrla connectors using @temp(Side1In)
        lines = ""

        line = "EQUATIONS 3\n"
        lines = lines + line
        line = "Tdp%dIn = $%s\n" % (idPort, connectorPort[idPort - 1]["T"])
        lines = lines + line
        line = "Mfrdp%d = $%s\n" % (idPort, connectorPort[idPort - 1]["Mfr"])
        lines = lines + line
        line = "Tdp%dInRev = $%s\n" % (idPort, connectorPort[idPort - 1]["Trev"])
        lines = lines + line

        return lines

    def getOnePortParConn(self, idPort, nTes, connectorPort):

        lines = "*********Connecting values of DIRECT PORT=%d***********\n" % (idPort + 1)

        line = "CONSTANTS 2\n"
        lines = lines + line

        line = "zInDp%d=%.2f\n" % (idPort + 1, connectorPort[idPort]["zIn"])
        lines = lines + line
        line = "zOutDp%d=%.2f\n" % (idPort + 1, connectorPort[idPort]["zOut"])
        lines = lines + line

        return lines

    def getOnePortPar(self, idPort, nTes):

        lines = "*********Constant of DIRECT PORT=%d***********\n" % (idPort + 1)

        line = "CONSTANTS 1\n"
        lines = lines + line
        line = "Dp%dStrat=0 ! 0: no forced stratification ; 1: force to stratify\n" % (idPort + 1)
        lines = lines + line

        return lines

    def getSensorPositionValues(self, nTes):

        lines = self.sLine + "** USER DEFINED TEMPERATURE SENSOR HEIGHTS. To be changed by user \n" + self.sLine

        line = "CONSTANTS 10\n"
        lines = lines + line

        z = 0.05
        for i in range(10):
            line = "zSen%d=%.2f\n" % (i + 1, z)
            lines = lines + line
            z = z + 0.1

        return lines

    def getOneHxParConnValues(self, nTes, idHx, connectHx):

        lines = "*********Connecting values of HX=%d***********\n" % idHx

        line = "CONSTANTS 4\n"
        lines = lines + line

        line = "zInhx%d=%.2f\n" % (idHx, connectHx[idHx - 1]["zIn"])
        lines = lines + line
        line = "zOuthx%d=%.2f\n" % (idHx, connectHx[idHx - 1]["zOut"])
        lines = lines + line
        line = "Cphx%d=$%s\n" % (idHx,  connectHx[idHx - 1]["cp"])
        lines = lines + line
        line = "Rhohx%d=$%s\n" % (idHx,  connectHx[idHx - 1]["rho"])
        lines = lines + line

        return lines

    @staticmethod
    def getOneHxParValues(nTes, idHx):

        lines = "*********Constant values of HX=%d***********\n" % idHx

        line = "CONSTANTS #\n"
        lines = lines + line

        line = "dInHx%d=0.05 ! m only if modHx%d=0\n" % (idHx,  idHx)
        lines = lines + line
        line = "dOutHx%d=0.06 ! m only if modHx%d=0\n" % (idHx, idHx)
        lines = lines + line
        line = "scaleHX%d=13 ! m only if modHx%d=0\n" % (idHx, idHx)
        lines = lines + line
        line = "LHx%d = scaleHX%d * Vol / (2 * $PI * 0.0333) ! m only if modHx%d=0\n" % (idHx, idHx, idHx)
        lines = lines + line
        line = "LamHx%d=50 ! W/mK only if modHx%d=0\n" % (idHx, idHx)
        lines = lines + line
        line = "brineConcHx%d=0 ! [0-100] only if modHx%d=0 TO BE MODIFIED IF GLYCOL USED\n" % (idHx, idHx)
        lines = lines + line

        line = "VHx%d=0. \n" % (idHx)
        lines = lines + line
        line = "nCvHx%d=20 \n" % (idHx)
        lines = lines + line

        line = "modHx%d=0 ! modHX1, 0 = physical model, 1 = Drueck-model (Multiport)\n" % (idHx)
        lines = lines + line
        line = "nNuHx%d=0.5 !  only if modHx%d=0\n" % (idHx, idHx)
        lines = lines + line
        line = "cNuHx%d=0.25 !  only if modHx%d=0\n" % (idHx, idHx)
        lines = lines + line

        line = "dUaMfrHx%d=0.375 ! only if modHx%d=1\n" % (idHx, idHx)
        lines = lines + line
        line = "dUadTHx%d=0.0 ! only if modHx%d=1\n" % (idHx, idHx)
        lines = lines + line
        line = "dUaTHx%d=0.458 ! only if modHx%d=1\n" % (idHx, idHx)
        lines = lines + line
        line = "UaHx%d=1105*ratio ! kJ/hK only if modHx%d=1\n" % (idHx, idHx)
        lines = lines + line
        line = "startUpHx%d=0. ! only if modHx%d=1\n" % (idHx, idHx)
        lines = lines + line

        return lines

    def getHxParValues(self, nTes, nHx):

        lines = ""
        for i in range(self.nMaxHx):
            idHx = i + 1
            line = "** Parameters for heat Exchanger number %d\n" % idHx
            lines = lines + line
            if idHx <= nHx:
                line = "zInHx%d " % (idHx)
                lines = lines + line
                line = "zOutHx%d " % (idHx)
                lines = lines + line
                line = "dInHx%d " % (idHx)
                lines = lines + line
                line = "dOutHx%d " % (idHx)
                lines = lines + line
                line = "LHx%d " % (idHx)
                lines = lines + line
                line = "LamHx%d " % (idHx)
                lines = lines + line
                line = "brineConcHx%d " % (idHx)
                lines = lines + line
                line = "VHx%d " % (idHx)
                lines = lines + line
                line = "CpHx%d " % (idHx)
                lines = lines + line
                line = "RhoHx%d " % (idHx)
                lines = lines + line
                line = "nCvHx%d " % (idHx)
                lines = lines + line
                line = "modHx%d " % (idHx)
                lines = lines + line
                line = "nNuHx%d " % (idHx)
                lines = lines + line
                line = "cNuHx%d " % (idHx)
                lines = lines + line
                line = "dUaMfrHx%d " % (idHx)
                lines = lines + line
                line = "dUadTHx%d " % (idHx)
                lines = lines + line
                line = "dUaTHx%d " % (idHx)
                lines = lines + line
                line = "UaHx%d " % (idHx)
                lines = lines + line
                line = "startUpHx%d ! Heax exchanger %d\n" % (idHx, idHx)
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

        line = "UaBot ! W/k \n"
        lines = lines + line
        line = "Uaz1  ! W/k\n"
        lines = lines + line
        line = "Uaz2  ! W/k\n"
        lines = lines + line
        line = "Uaz3  ! W/k\n"
        lines = lines + line
        line = "UaTop ! W/k\n"
        lines = lines + line

        return lines

    def getUaParValues(self, nTes, Ua):

        lines = ""
        line = "CONSTANTS 10\n"
        lines = lines + line

        line = "Ufoam= 0.67 ! W/(m2K) 6 cm of foam of 0.04 W/(mK) \n"
        lines = lines + line
        line = "Ubot = 1.5 ! W/(m2K) 2 cm of foam of 0.04 W/(mK)\n"
        lines = lines + line
        line = "Atop = Vol/Heigh ! m2\n"
        lines = lines + line
        line = "Diameter = (4*ATop/PI)^0.5 ! m \n"
        lines = lines + line
        line = "ALat = Heigh*PI*Diameter ! m2\n"
        lines = lines + line

        line = "UaBot= Ubot*ATop !  W/k \n"
        lines = lines + line
        line = "Uaz1 = Ufoam*ALat/3 !  W/k\n"
        lines = lines + line
        line = "Uaz2 = Ufoam*ALat/3 !  W/k\n"
        lines = lines + line
        line = "Uaz3 = Ufoam*ALat/3 !  W/k\n"
        lines = lines + line
        line = "UaTop = Ufoam*ATop !  W/k\n"
        lines = lines + line

        return lines

    def getFirst12Par(self, nTes):

        lines = ""
        line = "Vol     ! 1: m3, volume of store\n"
        lines = lines + line
        line = "RhoWat  ! 2: kg/m3, density of storage media\n"
        lines = lines + line
        line = "CpWat   ! 3: kJ/kgK, specific heat of storage media\n"
        lines = lines + line
        line = "lamZ    ! 4: W/mK, effective vertical thermal conductivity of TES\n"
        lines = lines + line
        line = "Heigh   ! 5: m, storage height\n"
        lines = lines + line
        line = "TIni   ! 6: oC, initial temperature\n"
        lines = lines + line
        line = "nCvMax  ! 7: -, minimum relative plug height\n"
        lines = lines + line
        line = "nCvMin  ! 8: -, maximum relative plug height\n"
        lines = lines + line
        line = "maxTDiff  ! 9: K, maximum temperature difference between plugs\n"
        lines = lines + line
        line = "readMode  ! 10: 1: from table, 0: Tini and CapTot\n"
        lines = lines + line
        line = "Tref     ! 11: oC, reference temperature\n"
        lines = lines + line

        return lines

    def getFirst12ParVar(self, nTes):

        lines = "CONSTANTS #\n"
        line = "Vol=1          ! 1: m3, volume of store\n"
        lines = lines + line
        # line = "RhoWat=RhoWat  ! 2: kg/m3, density of storage media\n"
        # lines = lines + line
        # line = "CpWat=CpWat    ! 3: kJ/kgK, specific heat of storage media\n"
        # lines = lines + line
        line = "lamZ=0.6       ! 4: W/mK, effective vertical thermal conductivity of TES\n"
        lines = lines + line
        line = "Heigh=1.       ! 5: m, storage height\n"
        lines = lines + line
        line = "Tini=60.       ! 6: oC, initial temperature\n"
        lines = lines + line
        line = "nCvMax=400     ! 7: -, minimum relative plug height\n"
        lines = lines + line
        line = "nCvMin=20      ! 8: -, maximum relative plug height\n"
        lines = lines + line
        line = "maxTDiff=0.015 ! 9: K, maximum temperature difference between plugs\n"
        lines = lines + line
        line = "readMode=0     ! 10: 1: from table, 0: Tini and CapTot\n"
        lines = lines + line
        line = "Tref=273.15    ! 11: oC, reference temperature\n"
        lines = lines + line
        line = "Tmax=100.       ! 6: oC, initial temperature\n"
        lines = lines + line

        line = self.getUaParValues(nTes, self.Ua)
        lines = lines + line

        return lines

    def getHeighDirectPortsPar(self, nPorts, nTes):

        lines = ""
        parId = 21
        for i in range(self.nMaxPorts):
            if i <= nPorts - 1:
                line = "zInDp%d zOutDp%d zero Dp%dStrat ! %d - %d: zIn, zOut, cp, strat\n" % (
                    i + 1,
                    i + 1,
                    i + 1,
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
            line = "zSen%d " % (i + 1)
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
                line = "zAux%d=%.2f\n" % (i + 1, connectorAux[i]["zAux"])
                lines = lines + line
                line = "qAux%d=%.2f\n" % (i + 1,  connectorAux[i]["qAux"])
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
                line = "zAux%d " % (i + 1)
                lines = lines + line
            else:
                line = "zero "
                lines = lines + line

        line = "\n"
        lines = lines + line

        return lines

    def getHeighAvgSensorParValues(self, nTes):

        lines = (
            self.sLine + "** USER DEFINED AVERAGED TEMPERATURE SENSOR HEIGHTS. To be changed by user \n" + self.sLine
        )

        line = "CONSTANTS 10\n"
        lines = lines + line
        z = 0.05
        for i in range(self.nMaxAvgSensor):
            line = "zSenAvgBot%d = %.2f\n" % (i + 1, z)
            lines = lines + line
            line = "zSenAvgTop%d = %.2f\n" % (i + 1, z + 0.1)
            lines = lines + line
            z = z + 0.2

        return lines

    def getHeighAvgSensorPar(self, nTes):

        lines = ""
        parId = 71
        for i in range(self.nMaxAvgSensor):
            line = (
                "zSenAvgBot%d zSenAvgTop%d ! %d-%d : relative position of lower and upper edge temeprature sensors\n"
                % (i + 1, i + 1,  parId, parId + 1)
            )
            lines = lines + line
            parId = parId + 2

        return lines

    def getInsulationPlateParValues(self, nTes):

        lines = "************* MOVING PLATE *******************\n"

        lines = lines + "CONSTANTS 4\n"

        line = (
            "MoInsPlate=0 ! 0-2, Insulation Plate Mode: 0 = no insulation plate inside TES, 1 = insulation plate at fixed relative height, 2 = insulation plate at fixed temperature / density controlled \n"
        )
        lines = lines + line
        line = (
            "zInsPlate=0  ! 0-1, relative position of fixed height insulation plate inside TES (only for Insulation Plate Mode = 1\n"
        )
        lines = lines + line
        line = (
            "TinsPlate=0  ! oC, temperature at which moveable insulation plate floats in TES (only for Insulation Plate Mode = 2)\n"
        )
        lines = lines + line
        line = (
            "UAinsPlate=0 ! W/K, overall heat transfer coefficient across moveable insulation plate (including heat transfer in gap between plate and wall and in wall at the respective height)\n"
        )
        lines = lines + line

        return lines

    def getInsulationPlatePar(self, nTes):

        lines = ""
        line = (
            "MoInsPlate ! 81: 0-2, Insulation Plate Mode: 0 = no insulation plate inside TES, 1 = insulation plate at fixed relative height, 2 = insulation plate at fixed temperature / density controlled \n"
        )
        lines = lines + line
        line = (
            "zInsPlate  ! 82: 0-1, relative position of fixed height insulation plate inside TES (only for Insulation Plate Mode = 1\n"
        )
        lines = lines + line
        line = (
            "TinsPlate  ! 83: oC, temperature at which moveable insulation plate floats in TES (only for Insulation Plate Mode = 2)\n"
        )
        lines = lines + line
        line = (
            "UAinsPlate ! 84: W/K, overall heat transfer coefficient across moveable insulation plate (including heat transfer in gap between plate and wall and in wall at the respective height)\n"
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
                line = "Tdp%dIn Mfrdp%d Tdp%dInRev\n" % (
                    idPort + 1,
                    idPort + 1,
                    idPort + 1,
                )

            else:
                line = "zero zero zero\n"
            lines = lines + line
        lines = lines + "****************\nTroomStore"  # This adds one input
        lines = lines + "\n***************** 6 HX INPUTS ******************\n"

        for idHx in range(self.nMaxHx):  # This adds 18 inputs
            if idHx <= nHx - 1:
                line = "Thx%dIn Mfrhx%d Thx%dInRev\n" % (
                    idHx + 1,
                    idHx + 1,
                    idHx + 1,
                )
            else:
                line = "zero zero zero\n"
            lines = lines + line
        lines = lines + "***************** 20 HEAT SOURCE INPUTS ******************\n"

        for i in range(20):  # This adds 20 inputs
            if i <= nHeatSources - 1:
                line = "qAux%d " % (i + 1)
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


    def getInputsFromOtherDdck(self,inputs):

        lines = self.sLine + "**inputs from other ddck\n" +self.sLine

        line = "CONSTANTS #\n"; lines = lines + line
        line = "RhoWat = $RhoWat  ! kg/m3, density of storage media\n"
        lines = lines + line
        line = "CpWat = $CpWat  ! kJ/kgK, specific heat of storage media\n"
        lines = lines + line
        line = "PI = $PI \n"
        lines = lines + line

        return lines

    def getOutputsToOtherDdck(self, inputs):

        nUnit = inputs["nUnit"]
        nTes = inputs["nTes"]
        nHx = inputs["nHx"]
        nPorts = inputs["nPorts"]

        lines = self.sLine + "**outputs to other ddck\n" +self.sLine

        line = "***Temperatures at 10 equally distributed height \n"
        lines = lines + line
        line = "EQUATIONS #\n"
        lines = lines + line

        counter = 21
        for i in range(10):
           height = 0.05 + 0.1 * i
           line = "$%s_T%d =[%d,%d] !temperature at %.2f \n" % (self.nameTes,i + 1, nUnit, counter, height)
           lines = lines + line
           counter = counter + 1

        line = "$%s_qHeatSource = qHeatSource \n"%self.nameTes
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
            line = "Qdp%d=[%d,%d] ! \n" % (idPort + 1, nUnit, 30 + idPort + 1)
            lines = lines + line

        nEq = 21
        line = "EQUATIONS #\n"
        lines = lines + line

        line = "TAvg = [%d,180] ! Average storage temperature \n" % ( nUnit)
        lines = lines + line
        #line = "***Temperatures at 10 equally distributed height \n"
        #lines = lines + line
        #counter = 21
        #for i in range(10):
        #    height = 0.05 + 0.1 * i
        #    line = "T%d =[%d,%d] !temperature at %.2f \n" % (i + 1, nUnit, counter, height)
        #    lines = lines + line
        #    counter = counter + 1

        line = "***Temperatures at 10 sensors user defined height\n"
        lines = lines + line
        counter = 71
        for i in range(10):
            line = "Tsen%d =[%d,%d] ! temperature at user defined sensor height Tsen%d \n" % (
                i + 1,
                nUnit,
                counter,
                i + 1,
            )
            lines = lines + line
            counter = counter + 1

        nEq = nHx
        if nEq > 0:
            line = "EQUATIONS %d\n" % nEq
            lines = lines + line

        counter = 102
        for idHx in range(nHx):
            line = "Qhx%dOut=[%d,%d] ! \n" % (idHx + 1, nUnit, counter + 2)
            lines = lines + line
            counter = counter + 10

        line = "EQUATIONS 1\n"
        lines = lines + line

        line = "qHeatSource = [%d,181] ! Heat input of all auxiliary heat sources [kW]\n" % (nUnit)
        lines = lines + line

        line = "EQUATIONS 5\n"
        lines = lines + line

        line = "Qv     = [%d,176] ! Heat input of all heat exchangers and auxiliary heat sources [kW]\n" % (
            nUnit,
        )
        lines = lines + line
        line = "QLoss  = [%d,177] ! Heat Losses of the Tes [kW]\n" % (nUnit)
        lines = lines + line
        line = "QAcum  = [%d,178] ! Sensible accumulated heat [kW]\n" % (nUnit)
        lines = lines + line
        line = "QPorts = [%d,179] ! Heat Input by direct ports [kW]\n" % (nUnit)
        lines = lines + line
        line = "QImb   = [%d,64]  ! Heat Imbalance in Tes  IMB = sumQv - sumQLoss -sumQAcum + sumQPort\n" % (
            nUnit,
        )
        lines = lines + line

        return lines

    def getMonthyPrinter(self, nTes, nUnit, inputs):

        nPrinterUnit = nUnit + 1
        lines = ""
        line = "CONSTANTS 1 \n"
        lines = lines + line
        line = "unitPrinter = %d \n" % (nPrinterUnit)
        lines = lines + line
        line = "ASSIGN temp\\TES%s_MO.dat unitPrinter\n" % (self.nameTes)
        lines = lines + line
        line = "UNIT %d TYPE 46\n" % nPrinterUnit
        lines = lines + line
        line = "PARAMETERS 5\n"
        lines = lines + line
        line = "unitPrinter ! 1: Logical unit number, -\n"
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

        inputsLine = "Qv QLoss QAcum QPorts QImb "
        for i in range(inputs["nPorts"]):
            nextInput = "Qdp%d " % (i + 1)
            inputsLine += nextInput

        for i in range(inputs["nHx"]):
            nextInput = "Qhx%dOut " % (i + 1)
            inputsLine += nextInput

        nextInput = "qHeatSource "
        inputsLine += nextInput

        lines += f"""\
{inputsLine}
{inputsLine}
"""

        return lines

    def getOnlinePlotter(self, nTes):

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
        line = "$nPlotsPerSim     ! 7 Number of plots per simulation \n"
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
        lineNames = "$%s_T1 $%s_T2 $%s_T3 $%s_T4 $%s_T5 $%s_T6 $%s_T7 $%s_T8 $%s_T9 $%s_T10 \n" %(self.nameTes,self.nameTes,self.nameTes,self.nameTes,self.nameTes,self.nameTes,self.nameTes,self.nameTes,self.nameTes,self.nameTes)
        lines = lines + lineNames
        lines = lines + lineNames
        line = "LABELS  3         \n"
        lines = lines + line
        line = "Temperatures  \n"
        lines = lines + line
        line = "Temperatures  \n"
        lines = lines + line
        line = "%s\n" % (self.nameTes)
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
        lines = lines + "tMax\n"
        lines = lines + "0\t0\t0 ! 17-20 unsused parameters\n"
        lines = lines + self.getHeighDirectPortsPar(nPorts, nTes)
        lines = lines + self.getHeighSensorPar(nTes)
        lines = lines + self.getHeighAvgSensorPar(nTes)
        lines = lines + self.getInsulationPlatePar(nTes)
        lines = lines + "nHxUsed     ! 85: number Of used Hx\n"

        lines = lines + self.getHxParValues(nTes, nHx)
        lines = lines + self.getPositionOfHeatSources(nTes, nHeatSources)
        lines = lines + self.getInputs(inputs)
        lines = lines + self.getOutputs(inputs)
        lines = lines + self.getMonthyPrinter(nTes, nUnit, inputs)
        lines = lines + self.getOnlinePlotter(nTes)
        return lines

    def getHead(self):

        header = open(r"C:\Daten\OngoingProject\SolTherm2050\Simulations\ddck\Generic\Head.ddck", "r")
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
            lines = lines + "** check cp and rho values for the circuits \n"
            lines = lines + "** default is cpwat and rhowat, for solarcirc usually cpbri and rhobri have to be used \n"
            lines = lines + self.sLine + "\n"
            lines = lines + self.sLine
            lines = lines + "** outputs to energy balance in kWh\n"

            lines = lines + self.sLine
            lines = lines + "EQUATIONS 3\n"

            lines = lines + ("@energy(out, heat, %sLoss) = QLoss\n" % tankName)
            lines = lines + ("@energy(out, heat, %sAcum) = QAcum\n" % (tankName))
            lines = lines + ("@energy(in, el, %sAux)     = qHeatSource\n" % (tankName))

           # lines = lines + ("qSysOut_%sLoss = QLoss_Tes%d\n" % (tankName, self.inputs["nTes"]))
           # lines = lines + ("qSysOut_%sAcum = QAcum_Tes%d\n" % (tankName, self.inputs["nTes"]))
           # lines = lines + ("elSysIn_Q_%sAux = qHeatSource_Tes%d\n" % (tankName, self.inputs["nTes"]))

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

        for idPort in range(nPorts):
            line = self._getOnePortInputs(nTes, idPort + 1, self.connectorsPort)
            lines = lines + line

        for idHx in range(nHxs):
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
        for port in self.connectorsPort:
            outputTemperature = port["Tout"]
            line = f"${outputTemperature}=[{nUnit},{counter}]\n"
            lines = lines + line
            counter = counter + 2

        nEq = nHxs
        if nEq > 0:
            line = "EQUATIONS %d\n" % nEq
            lines = lines + line
            line = "*** heat exchanger outputs\n"
            lines = lines + line

        counter = 102
        for hx in self.connectorsHx:
            outputTemperature = hx["Tout"]
            line = f"${outputTemperature}=[{nUnit},{counter}]\n"
            lines = lines + line
            counter = counter + 10

        lines = lines + "\n"
        lines = lines + self.getInputsFromOtherDdck(self.inputs)

        lines = lines + "\n"
        lines = lines + self.getOutputsToOtherDdck(self.inputs)


        line = self.sLine + "****** Parameters of Type1924 *******\n" + self.sLine
        lines = lines + line

        lines = lines + "CONSTANTS #\n"

        line = "zero=0.0 ! \n"
        lines = lines + line
        line = "TRoomStore=15 ! \n"
        lines = lines + line
        line = "VStoreRef = 0.763\n"
        lines = lines + line
        line = "ratio = Vol / VStoreRef\n"
        lines = lines + line

        for idPort in range(nPorts):
            line = self.getOnePortParConn(idPort, nTes, self.connectorsPort)
            lines = lines + line

        for idHx in range(nHxs):
            line = self.getOneHxParConnValues(nTes, idHx + 1, self.connectorsHx)
            lines = lines + line

        for idPort in range(nPorts):
            line = self.getOnePortPar(idPort, nTes)
            lines = lines + line

        lines = lines + "********** HEAT EXCHANGER CONSTANTS*******\n"
        lines = lines + "CONSTANTS 1\n"
        lines = lines + "nHxUsed=%d \n" % (nHxs)

        for idHx in range(nHxs):
            line = self.getOneHxParValues(nTes, idHx + 1)
            lines = lines + line

        lines = lines + self.getSensorPositionValues(nTes)
        lines = lines + self.getHeighAvgSensorParValues(nTes)

        lines = lines + self.getFirst12ParVar(nTes)
        lines = lines + self.getInsulationPlateParValues(nTes)
        lines = lines + self.getParameters(self.inputs)

        outputFilePath = _pl.Path(path) / f"{tankName}.{self.extension}"
        outputFilePath.write_text(lines)
