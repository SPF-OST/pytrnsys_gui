
import os
import numpy as num

class Type1924_TesPlugFlow():

    def __init__(self):

        self.listParHx  = ["","","",""]
        self.listParPort= num.zeros(10)
        self.listParUa  = num.zeros(10)

        self.nMaxPorts=10
        self.nMaxHx=6
        self.nMaxSensor=10
        self.nMaxAvgSensor=5

        self.sLine="*****************************************************\n"
        self.extension="ddck"

    def setInputs(self,inputs,connectorsPort,connectorsHx,connectorsAux):

        self.inputs=inputs
        self.connectorsPort=connectorsPort
        self.connectorsHx=connectorsHx
        self.connectorsAux=connectorsAux


    def getOneHxInputs(self,nTes,idHx,connectorHx):

        lines = ""

        line = "EQUATIONS 3\n";lines=lines+line
        line = "Thx%dIn_Tes%d = %s ! @connectDdck\n"%(idHx,nTes,connectorHx[idHx-1]["T"]);lines=lines+line
        line = "Mfrhx%d_Tes%d = %s ! @connectDdck\n"%(idHx,nTes,connectorHx[idHx-1]["Mfr"]);lines=lines+line
        line = "Thx%dInRev_Tes%d = %s ! @connectDdck\n"%(idHx,nTes,connectorHx[idHx-1]["Trev"]);lines=lines+line

        return lines

    def getOnePortInputs(self,nTes,idPort,connectorPort):

        lines = ""

        line = "EQUATIONS 3\n";lines=lines+line
        line = "Tdp%dIn_Tes%d = %s ! @connectDdck\n"%(idPort,nTes,connectorPort[idPort-1]["T"]);lines=lines+line
        line = "Mfrdp%d_Tes%d = %s ! @connectDdck\n"%(idPort,nTes,connectorPort[idPort-1]["Mfr"]);lines=lines+line
        line = "Tdp%dInRev_Tes%d = %s ! @connectDdck\n"%(idPort,nTes,connectorPort[idPort-1]["Trev"]);lines=lines+line

        return lines

    def getOnePortParConn(self,idPort,nTes,connectorPort):

        lines = "*********Connecting values of DIRECT PORT=%d***********\n"%(idPort+1)

        line = "CONSTANTS 2\n";lines=lines+line

        line = "zInDp%d_Tes%d=%.2f ! @connectDdck \n"%(idPort+1,nTes,connectorPort[idPort]["zIn"]);lines=lines+line
        line = "zOutDp%d_Tes%d=%.2f ! @connectDdck \n"%(idPort+1,nTes,connectorPort[idPort]["zOut"]);lines=lines+line

        return lines

    def getOnePortPar(self, idPort, nTes):

        lines = "*********Constant of DIRECT PORT=%d***********\n" % (idPort + 1)

        line = "CONSTANTS 2\n";lines=lines+line
        line = "cpDp%d_Tes%d=zero \n"%(idPort+1,nTes);lines=lines+line
        line = "Dp%dStrat_Tes%d=0 ! 0: no forced stratification ; 1: force to stratify\n"%(idPort+1,nTes);lines=lines+line


        # count=0
        # for line in myList:
        #     splitEqual=line.split("=")
        #     if(len(splitEqual)>1):
        #         par = splitEqual[0]
        #         if(count==0):
        #             self.listParPort[nPort-1]=par
        #         else:
        #             self.listParPort[nPort-1] = self.listParPort[nPort-1] + " " + par
        #         count=count+1

        return lines

    def getSensorPositionValues(self,nTes):

        lines=self.sLine+"** USER DEFINED TEMPERATURE SENSOR HEIGHTS. To be changed by user \n"+self.sLine

        line="CONSTANTS 10\n";lines=lines+line

        z=0.05
        for i in range(10):
            line = "zSen%d_Tes%d=%.2f\n" %(i+1,nTes,z); lines=lines+line
            z=z+0.1

        return lines

    def getOneHxParConnValues(self, nTes, idHx, connectHx):

        lines = "*********Connecting values of HX=%d***********\n"%idHx

        line = "CONSTANTS 4\n";lines=lines+line

        line = "zInhx%d_Tes%d=%.2f  ! @connectDdck\n"%(idHx,nTes,connectHx[idHx-1]["zIn"]);lines=lines+line
        line = "zOuthx%d_Tes%d=%.2f ! @connectDdck\n"%(idHx,nTes,connectHx[idHx-1]["zOut"]);lines=lines+line
        line = "Cphx%d_Tes%d=%s     ! @connectDdck\n"%(idHx,nTes,connectHx[idHx-1]["cp"]);lines=lines+line
        line = "Rhohx%d_Tes%d=%s    ! @connectDdck\n"%(idHx,nTes,connectHx[idHx-1]["rho"]);lines=lines+line

        return lines

    def getOneHxParValues(self, nTes, idHx):


        lines = "*********Constant values of HX=%d***********\n"%idHx

        line = "CONSTANTS 15\n";lines=lines+line

        line = "dInHx%d_Tes%d=0.05 ! m only if modHx%d=1\n"%(idHx,nTes,idHx);lines=lines+line
        line = "dOutHx%d_Tes%d=0.06 ! m only if modHx%d=1\n"%(idHx,nTes,idHx);lines=lines+line

        line = "LHx%d_Tes%d=20 ! m only if modHx%d=1\n"%(idHx,nTes,idHx);lines=lines+line
        line = "LamHx%d_Tes%d=50 ! W/mK only if modHx%d=1\n"%(idHx,nTes,idHx);lines=lines+line
        line = "brineConcHx%d_Tes%d=30 ! [0-100] only if modHx%d=1\n"%(idHx,nTes,idHx);lines=lines+line

        line = "VHx%d_Tes%d=0. \n"%(idHx,nTes);lines=lines+line
        line = "nCvHx%d_Tes%d=20 \n"%(idHx,nTes);lines=lines+line

        line = "modHx%d_Tes%d=1 ! modHX1, 0 = physical model, 1 = Drueck-model (Multiport)\n"%(idHx,nTes);lines=lines+line
        line = "nNuHx%d_Tes%d=0.5 !  only if modHx%d=1\n"%(idHx,nTes,idHx);lines=lines+line
        line = "cNuHx%d_Tes%d=0.25 !  only if modHx%d=1\n"%(idHx,nTes,idHx);lines=lines+line

        line = "dUaMfrHx%d_Tes%d=0.375 ! only if modHx%d=0\n"%(idHx,nTes,idHx);lines=lines+line
        line = "dUadTHx%d_Tes%d=0.0 ! only if modHx%d=0\n"%(idHx,nTes,idHx);lines=lines+line
        line = "dUaTHx%d_Tes%d=0.458 ! only if modHx%d=0\n"%(idHx,nTes,idHx);lines=lines+line
        line = "UaHx%d_Tes%d=1105 ! kJ/hK only if modHx%d=0\n"%(idHx,nTes,idHx);lines=lines+line

        line = "startUpHx%d_Tes%d=0. ! only if modHx%d=0\n"%(idHx,nTes,idHx);lines=lines+line

        return lines

        # count=0
        # self.listParHx[idHx-1]=""
        #
        # for line in myList:
        #     splitEqual=line.split("=")
        #     if(len(splitEqual)>1):
        #         par = splitEqual[0]
        #         if(count==0):
        #             self.listParHx[idHx-1]=par
        #         else:
        #             self.listParHx[idHx-1] = self.listParHx[idHx-1] + " " + par
        #         count=count+1


    def getHxParValues(self, nTes, nHx):

        lines=""
        for i in range(self.nMaxHx):
            idHx=i+1
            line = "** Parameters for heat Exchanger number %d\n"%idHx;lines=lines+line
            if(idHx<=nHx):
                line = "zInHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "zOutHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "dInHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "dOutHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "LHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "LamHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "brineConcHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "VHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "CpHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "RhoHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "nCvHx%d_Tes%d " %(idHx,nTes);lines=lines+line
                line = "modHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "nNuHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "cNuHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "dUaMfrHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "dUadTHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "dUaTHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "UaHx%d_Tes%d "%(idHx,nTes);lines=lines+line
                line = "startUpHx%d_Tes%d ! Heax exchanger %d\n"%(idHx,nTes,idHx);lines=lines+line
            else:
                for i in range(19):
                    line="zero ";lines=lines+line
                lines=lines+"! Heax exchanger %d\n"%(idHx)

        return lines

    # def getOnePortPar(self,nTes,nPort):
    #
    #     lines = ""
    #
    #     line = "EQUATIONS 3\n";lines=lines+line
    #     line = "Tdp%d_Tes%d = @connect\n"%(nPort,nTes);lines=lines+line
    #     line = "Mfrdp%d_Tes%d = @connect\n"%(nPort,nTes);lines=lines+line
    #     line = "TdpRev%d_Tes%d = @connect\n"%(nPort,nTes);lines=lines+line
    #
    #     return lines

    def getUaPar(self,nTes):

        lines = ""

        line = "UaBot_Tes%d ! W/k \n"%(nTes);lines=lines
        line = "Uaz1_Tes%d  ! W/k\n"%(nTes);lines=lines
        line = "Uaz2_Tes%d  ! W/k\n"%(nTes);lines=lines
        line = "Uaz3_Tes%d  ! W/k\n"%(nTes);lines=lines
        line = "UaTop_Tes%d ! W/k\n"%(nTes);lines=lines

        return lines

    def getUaParValues(self,nTes,Ua):

        lines = ""
        myList =[]
        line = "CONSTANTS 5\n";lines=lines+line

        line = "UaBot_Tes%d= 1 ! W/k \n"%(nTes,Ua[0]);lines=lines+line
        line = "Uaz1_Tes%d = 1 ! W/k\n"%(nTes,Ua[1]);lines=lines+line
        line = "Uaz2_Tes%d = 1 ! W/k\n"%(nTes,Ua[2]);lines=lines+line
        line = "Uaz3_Tes%d = 1 ! W/k\n"%(nTes,Ua[3]);lines=lines+line
        line = "UaTop_Tes%d = 1 ! W/k\n"%(nTes,Ua[4]);lines=lines+line

        return lines

    def getFirst12Par(self,nTes):

        lines=""
        line = "Vol_Tes%d     ! 1: m3, volume of store\n"%nTes;lines=lines+line
        line = "RhoWat_Tes%d  ! 2: kg/m3, density of storage media\n"%nTes;lines=lines+line
        line = "CpWat_Tes%d   ! 3: kJ/kgK, specific heat of storage media\n"%nTes;lines=lines+line
        line = "lamZ_Tes%d    ! 4: W/mK, effective vertical thermal conductivity of TES\n"%nTes;lines=lines+line
        line = "Heigh_Tes%d   ! 5: m, storage height\n"%nTes;lines=lines+line
        line = "TIni_Tes%d   ! 6: °C, initial temperature\n"%nTes;lines=lines+line
        line = "nCvMax_Tes%d  ! 7: -, minimum relative plug height\n"%nTes;lines=lines+line
        line = "nCvMin_Tes%d  ! 8: -, maximum relative plug height\n"%nTes;lines=lines+line
        line = "maxTDiff_Tes%d  ! 9: K, maximum temperature difference between plugs\n"%nTes;lines=lines+line
        line = "readMode_Tes%d  ! 10: 1: from table, 0: Tini and CapTot\n"%nTes;lines=lines+line
        line = "Tref_Tes%d     ! 11: °C, reference temperature\n"%nTes;lines=lines+line

        return lines

    def getFirst12ParVar(self,nTes):

        lines="CONSTANTS 12\n"
        line = "Vol_Tes%d=1          ! 1: m3, volume of store\n"%nTes;lines=lines+line
        line = "RhoWat_Tes%d=RhoWat  ! 2: kg/m3, density of storage media\n"%nTes;lines=lines+line
        line = "CpWat_Tes%d=CpWat    ! 3: kJ/kgK, specific heat of storage media\n"%nTes;lines=lines+line
        line = "lamZ_Tes%d=0.6       ! 4: W/mK, effective vertical thermal conductivity of TES\n"%nTes;lines=lines+line
        line = "Heigh_Tes%d=1.       ! 5: m, storage height\n"%nTes;lines=lines+line
        line = "Tini_Tes%d=60.       ! 6: °C, initial temperature\n"%nTes;lines=lines+line
        line = "nCvMax_Tes%d=400     ! 7: -, minimum relative plug height\n"%nTes;lines=lines+line
        line = "nCvMin_Tes%d=20      ! 8: -, maximum relative plug height\n"%nTes;lines=lines+line
        line = "maxTDiff_Tes%d=0.015 ! 9: K, maximum temperature difference between plugs\n"%nTes;lines=lines+line
        line = "readMode_Tes%d=0     ! 10: 1: from table, 0: Tini and CapTot\n"%nTes;lines=lines+line
        line = "Tref_Tes%d=273.15    ! 11: °C, reference temperature\n"%nTes;lines=lines+line
        line = "Tmax_Tes%d=100.       ! 6: °C, initial temperature\n"%nTes;lines=lines+line

        return lines


    def getHeighDirectPortsPar(self,nPorts,nTes):

        lines=""
        parId=21
        for i in range(self.nMaxPorts):
            if(i<=nPorts-1):
                line="zInDp%d_Tes%d zOutDp%d_Tes%d zero Dp%dStrat_Tes%d ! %d - %d: zIn, zOut, cp, strat\n"%(i+1,nTes,i+1,nTes,i+1,nTes,parId,parId+4)
                lines=lines+line
            else:
                line="zero zero zero zero ! %d - %d: zIn, zOut, cp, strat\n"%(parId,parId+4)
                lines = lines + line

            parId=parId+5

        return lines

    def getHeighSensorPar(self,nTes):

        lines = ""
        parId = 61
        for i in range(self.nMaxSensor):
            line="zSen%d_Tes%d "%(i+1,nTes);lines=lines+line

        line="! %d-%d : relative storage temperature sensor heights \n"%(parId, parId + 10)
        lines=lines+line

        return lines

    def getHeatSourcesValues(self,nTes,nHeatSources,connectorAux):

        lines=""
        line=self.sLine+"************ AUXILIAR HEATING**********\n"
        line="CONSTANTS=%d\n"%(nHeatSources*2);lines=lines+line

        for i in range(nHeatSources):
            line="zAux%d_Tes%d=%.2f !connectDDck\n" %(i+1,nTes,connectorAux[i]["zAux"]);lines=lines+line
            line="qAux%d_Tes%d=%.2f !connectDDck\n" %(i+1,nTes,connectorAux[i]["qAux"]);lines=lines+line

        line = "\n";lines = lines + line

        return lines


    def getPositionOfHeatSources(self,nTes,nHeatSources):

        lines=""
        line="** 20 height position for any heat source, e.g. electrical backup or heat pump condenser. Any position can be due to a different heat source\n";lines=lines+line
        for i in range(20):
            if(i<=nHeatSources-1):
                line="zAux%d_Tes%d "%(i+1,nTes);lines=lines+line
            else:
                line="zero ";lines=lines+line

        line = "\n";lines = lines + line

        return lines

    def getHeighAvgSensorParValues(self,nTes):

        lines=self.sLine+"** USER DEFINED AVERAGED TEMPERATURE SENSOR HEIGHTS. To be changed by user \n"+self.sLine

        line="CONSTANTS 10\n";lines=lines+line
        z=0.05
        for i in range(self.nMaxAvgSensor):
            line="zSenAvgBot%d_Tes%d = %.2f\n"%(i+1,nTes,z);lines=lines+line
            line="zSenAvgTop%d_Tes%d = %.2f\n"%(i+1,nTes,z+0.1);lines=lines+line
            z=z+0.2

        return lines

    def getHeighAvgSensorPar(self,nTes):

        lines = ""
        parId = 71
        for i in range(self.nMaxAvgSensor):
            line="zSenAvgBot%d_Tes%d zSenAvgTop%d_Tes%d ! %d-%d : relative position of lower and upper edge temeprature sensors\n"%(i+1,nTes,i+1,nTes,parId,parId+1);lines=lines+line
            parId=parId+2



        return lines


    def getInsulationPlateParValues(self,nTes):

        lines="************* MOVING PLATE *******************\n"

        lines=lines+"CONSTANTS 4\n"

        line="MoInsPlate_Tes%d=0 ! 0-2, Insulation Plate Mode: 0 = no insulation plate inside TES, 1 = insulation plate at fixed relative height, 2 = insulation plate at fixed temperature / density controlled \n"%nTes
        lines=lines+line
        line="zInsPlate_Tes%d=0  ! 0-1, relative position of fixed height insulation plate inside TES (only for Insulation Plate Mode = 1\n"%nTes;lines=lines+line
        line="TinsPlate_Tes%d=0  ! °C, temperature at which moveable insulation plate floats in TES (only for Insulation Plate Mode = 2)\n"%nTes;lines=lines+line
        line="UAinsPlate_Tes%d=0 ! W/K, overall heat transfer coefficient across moveable insulation plate (including heat transfer in gap between plate and wall and in wall at the respective height)\n"%nTes;lines=lines+line


        return lines

    def getInsulationPlatePar(self,nTes):

        lines=""
        line="MoInsPlate_Tes%d ! 81: 0-2, Insulation Plate Mode: 0 = no insulation plate inside TES, 1 = insulation plate at fixed relative height, 2 = insulation plate at fixed temperature / density controlled \n"%nTes
        lines=lines+line
        line="zInsPlate_Tes%d  ! 82: 0-1, relative position of fixed height insulation plate inside TES (only for Insulation Plate Mode = 1\n"%nTes;lines=lines+line
        line="TinsPlate_Tes%d  ! 83: °C, temperature at which moveable insulation plate floats in TES (only for Insulation Plate Mode = 2)\n"%nTes;lines=lines+line
        line="UAinsPlate_Tes%d ! 84: W/K, overall heat transfer coefficient across moveable insulation plate (including heat transfer in gap between plate and wall and in wall at the respective height)\n"%nTes;lines=lines+line

        return lines

    def getInputs(self,inputs):

        nHx=inputs["nHx"]
        nTes=inputs["nTes"]
        nPorts=inputs["nPorts"]
        nHeatSources=inputs["nHeatSources"]

        lines=""
        line = "INPUTS 69\n";lines=lines+line
        line = "************10 DIRECT PORTS INPUTS***************\n";lines=lines+line

        for idPort in range(self.nMaxPorts):
            if(idPort<=nPorts-1):
                line = "Tdp%dIn_Tes%d Mfrdp%d_Tes%d Tdp%dInRev_Tes%d\n" % (idPort+1,nTes,idPort+1,nTes,idPort+1,nTes)
                lines = lines + line

            else:
                line = "zero zero zero\n"
                lines = lines + line
        lines = lines + "****************\nTroomStore"
        lines = lines + "\n***************** 6 HX INPUTS ******************\n"

        for idHx in range(self.nMaxHx):
            if(idHx<=nHx-1):
                line = "Thx%dIn_Tes%d Mfrhx%d_Tes%d Thx%dInRev_Tes%d\n" % (idHx+1,nTes,idHx+1,nTes,idHx+1,nTes)
            else:
                line = "zero zero zero\n"
            lines = lines + line
        lines = lines + "***************** 20 HEAT SOURCE INPUTS ******************\n"

        for i in range(20):
            if(i<=nHeatSources-1):
                line = "qHeatSource%d_Tes%d " % (i+1,nTes)
            else:
                line = "zero "
            lines = lines + line
        lines = lines + "\n"

        return lines

    def getOutputs(self,inputs):

        nUnit=inputs["nUnit"]
        nTes=inputs["nTes"]
        nHx=inputs["nHx"]
        nPorts=inputs["nPorts"]

        lines="*****************OUTPUTS****************\n"

        nEq = nPorts*2
        line="EQUATIONS %d\n"%nEq;lines=lines+line

        counter=1
        for idPort in range(nPorts):
            line="Tdp%dOut_Tes%d=[%d,%d] ! \n"%(idPort+1,nTes,nUnit,counter);lines=lines+line
            line="Qdp%d_Tes%d=[%d,%d] ! \n"%(idPort+1,nTes,nUnit,counter+30);lines=lines+line
            counter=counter+2

        nEq = 21
        line="EQUATIONS %d\n"%nEq;lines=lines+line

        line="TAvg_Tes%d = [%d,180] ! Average storage temperature \n"%(nTes,nUnit);lines=lines+line
        line="***Temperatures at 10 equallay distributed height \n";lines=lines+line
        counter=21
        for i in range(10):
            height=0.05+0.1*i
            line ="T%d_Tes%d =[%d,%d] !temperature at %.2f \n"%(i+1,nTes,nUnit,counter,height);lines=lines+line
            counter=counter+1

        line="***Temperatures at 10 sensors user defined height\n";lines=lines+line
        counter=71
        for i in range(10):
            line ="Tsen%d_Tes%d =[%d,%d] ! temperature at user defined sensor height Tsen%d_Tes%d \n"%(i+1,nTes,nUnit,counter,i+1,nTes);lines=lines+line
            counter=counter+1

        # line="***Temperatures at 5 sensor averaged user defined height\n";lines=lines+line
        # counter=81
        # for i in range(10):
        #     line ="**TsenAvg%d_Tes%d =[%d,%d] !temperature at average sensor zsenAvg%d_Tes%d"%(i+1,nTes,nUnit,counter,i+1,nTes)
        #     counter=counter+1

        nEq = nHx*2
        line="EQUATIONS %d\n"%nEq;lines=lines+line

        counter=102
        for idHx in range(nHx):
            line="Thx%dOut_Tes%d=[%d,%d] ! \n"%(idHx+1,nTes,nUnit,counter);lines=lines+line
            line="Qhx%dOut_Tes%d=[%d,%d] ! \n"%(idHx+1,nTes,nUnit,counter+2);lines=lines+line
            counter=counter+10

        line="EQUATIONS 1\n";lines=lines+line

        line = "qHeatSource_Tes%d = [%d,181] ! Heat input of all auxiliary heat sources [kW]\n"%(nTes,nUnit);lines=lines+line

        line="EQUATIONS 5\n";lines=lines+line

        line = "sumQv_Tes%d     = [%d,176] ! Heat input of all heat exchangers [kW]\n"%(nTes,nUnit);lines=lines+line
        line = "sumQLoss_Tes%d  = [%d,177] ! Heat Losses of the Tes [kW]\n"%(nTes,nUnit);lines=lines+line
        line = "sumQAcum_Tes%d  = [%d,178] ! Sensible accumulated heat [kW]\n"%(nTes,nUnit);lines=lines+line
        line = "sumQPorts_Tes%d = [%d,179] ! Heat Input by direct ports [kW]\n"%(nTes,nUnit);lines=lines+line
        line = "Imb_Tes%d       = [%d,64]  ! Heat Imbalance in Tes  IMB = sumQv - sumQLoss -sumQAcum + sumQPort\n"%(nTes,nUnit);lines=lines+line

        return lines

    def getParameters(self,inputs):

        nUnit=inputs["nUnit"]
        nType=inputs["nType"]
        nTes=inputs["nTes"]
        nPorts=inputs["nPorts"]
        nHx=inputs["nHx"]
        nHeatSources=inputs["nHeatSources"]

        Ua=[1,1,1,1]

        lines=self.sLine+"**************** TYPE DEFINITION ********************\n"+self.sLine

        lines=lines+"UNIT %d TYPE %d     ! plug flow tank\n"%(nUnit,nType)
        lines = lines + "PARAMETERS 219 \n"
        lines=lines+self.getFirst12Par(nTes)
        lines=lines+self.getUaPar(nTes)
        lines=lines+"tMax_Tes%d\n"%nTes
        lines=lines+"0\t0\t0 ! 17-20 unsused parameters\n"
        lines=lines+self.getHeighDirectPortsPar(nPorts,nTes)
        lines=lines+self.getHeighSensorPar(nTes)
        lines=lines+self.getHeighAvgSensorPar(nTes)
        lines=lines+self.getInsulationPlatePar(nTes)
        lines=lines+"nHxUsed_Tes%d     ! 85: number Of used Hx\n"%nTes

        lines=lines+self.getHxParValues(nTes,nHx)
        lines=lines+self.getPositionOfHeatSources(nTes,nHeatSources)
        lines=lines + self.getInputs(inputs)
        lines=lines + self.getOutputs(inputs)

        return lines

    def getHead(self):

        header = open("C:\Daten\OngoingProject\SolTherm2050\Simulations\ddck\Generic\Head.ddck", "r")
        lines=header.read()
        header.close()

        return lines
    def createDDck(self, path, name,typeFile="ddck"):

        lines=""
        if(typeFile=="ddck"):
            self.extension="ddck"

        elif(typeFile=="dck"):
            self.extension="dck"
            lines = self.getHead()
        else:
            raise ValueError("typeFile %s unknown (Must be dck or ddck)")

        lines=lines+self.sLine+"**************** Inputs from hydraulic solver ********************\n"+self.sLine

        nTes = self.inputs["nTes"]
        nHxs = self.inputs["nHx"]
        nPorts = self.inputs["nPorts"]
        nAux = self.inputs["nHeatSources"]

        for idPort in range(self.nMaxPorts):
            if (idPort <= nPorts - 1):
                line = self.getOnePortInputs(nTes, idPort + 1, self.connectorsPort)
                lines = lines + line

        for idHx in range(self.nMaxHx):
            if (idHx <= nHxs - 1):
                line = self.getOneHxInputs(nTes, idHx + 1, self.connectorsHx)
                lines = lines + line

        line=self.getHeatSourcesValues(nTes, nAux, self.connectorsAux)
        lines = lines + line

        line  = self.sLine+"**************** Parameters of Type1924 ********************\n"+self.sLine
        lines = lines+line

        for idPort in range(self.nMaxPorts):
            if (idPort <= nPorts - 1):

                line = self.getOnePortParConn(idPort, nTes, self.connectorsPort)
                lines = lines + line

        for idHx in range(self.nMaxHx):
            if (idHx <= nHxs - 1):
                line = self.getOneHxParConnValues(nTes, idHx + 1, self.connectorsHx)
                lines = lines + line


        for idPort in range(self.nMaxPorts):
            if (idPort <= nPorts - 1):

                line = self.getOnePortPar(idPort, nTes)
                lines = lines + line

        lines = lines + "********** HEAT EXCHANGER CONSTANTS*******\n"
        lines = lines + "CONSTANTS 1\n"
        lines=lines+"nHxUsed_Tes%d=%d \n"%(nTes,nHxs)

        for idHx in range(self.nMaxHx):
            if (idHx <= nHxs - 1):
                line = self.getOneHxParValues(nTes, idHx + 1)
                lines = lines + line

        lines = lines + self.getSensorPositionValues(nTes)
        lines = lines + self.getHeighAvgSensorParValues(nTes)

        lines = lines + self.getFirst12ParVar(nTes)
        lines = lines + self.getInsulationPlateParValues(nTes)
        lines = lines + self.getParameters(self.inputs)

        nameWithPath = '%s\%s.%s' % (path, name,self.extension)
        outfile = open(nameWithPath, 'w')
        outfile.writelines(lines)
        outfile.close()


if __name__ == '__main__':

    path = "C:\Daten\OngoingProject\SolTherm2050\Simulations\ddck\Tes"
    name = "Type1924_automatic"

    tool = Type1924_TesPlugFlow()

    inputs={"nUnit":50,
            "nType":1924,
            "nTes":1,
            "nPorts":2,
            "nHx":2,
            "nHeatSources":1
            }

    dictInput={"T":"Null","Mfr":"Null","Trev":"Null","zIn":0.0,"zOut":0.0}
    dictInputHx={"T":"Null","Mfr":"Null","Trev":"Null","zIn":0.0,"zOut":0.0,"cp":0.0,"rho":0.0}
    dictInputAux={"zAux":0.0,"qAux":0.0}

    connectorsPort=[]
    connectorsHx=[]
    connectorsAux=[]

    for i in range(inputs["nPorts"]):
        connectorsPort.append(dictInput)

    for i in range(inputs["nHx"]):
        connectorsHx.append(dictInputHx)

    for i in range(inputs["nHeatSources"]):
        connectorsAux.append(dictInputAux)

    connectorsPort[0]= {"T":"60.","Mfr":"2000","Trev":"0","zIn":0.99,"zOut":0.01}
    connectorsPort[1]= {"T":"10.","Mfr":"1000","Trev":"0","zIn":0.05,"zOut":0.95}

    connectorsHx[0] = {"T":"50.","Mfr":"800","Trev":"0","zIn":0.9,"zOut":0.5,"cp":"cpWat","rho":"rhoWat"}
    connectorsHx[1] = {"T":"30.","Mfr":"500","Trev":"0","zIn":0.4,"zOut":0.2,"cp":"cpWat","rho":"rhoWat"}

    connectorsAux[0] = {"zAux":0.7,"qAux":3000}

    tool.setInputs(inputs,connectorsPort,connectorsHx,connectorsAux)

    tool.createDDck(path,name,typeFile="dck")

