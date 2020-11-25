import re
import string
import os
import sys

from PyQt5.QtWidgets import QMessageBox

from trnsysGUI.Connection import Connection
from trnsysGUI.Pump import Pump
from trnsysGUI.TVentil import TVentil
from trnsysGUI.WTap_main import WTap_main
from trnsysGUI.StorageTank import StorageTank
from trnsysGUI.Connector import Connector
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.Collector import Collector


class Export(object):
    def __init__(self, objList, editor):
        self.trnsysObj = objList
        self.editor = editor
        self.maxChar = 20

        self.lineNumOfPar = 0
        for component in self.trnsysObj:
            numOfRelPorts = 0
            if isinstance(component,StorageTank) or (isinstance(component,Connection) and (type(component.fromPort.parent) is StorageTank or type(component.toPort.parent) is StorageTank)):
                pass
            elif isinstance(component,Connection):
                numOfRelPorts = 1
            else:
                try:
                    numOutputs = len(component.outputs)
                except:
                    pass
                try:
                    numInputs = len(component.inputs)
                except:
                    pass
                if numOutputs + numInputs <= 1:
                    numOfRelPorts = numOutputs + numInputs
                else:
                    numOfRelPorts = min(numOutputs,numInputs)
            self.lineNumOfPar += numOfRelPorts
        self.numOfPar = 4*self.lineNumOfPar+1

    def connectionExplorer(self):
        connectionDict = {}
        connectionDictNum = {}

        numOfStorageTanks = 0
        for t in self.trnsysObj:
            # if isinstance(t,StorageTank):
            #     numOfStorageTanks += 1
            #     tesName = "Tes_%s" % numOfStorageTanks
            #     connectionDict[tesName] =  [t.trnsysId, '','']
            #     connectionDictNum[str(t.trnsysId)] = tesName
            #     for p in t.inputs + t.outputs:
            #         if not(p.isFromHx):
            #             if p.side == 0:
            #                 lr = "Left"
            #             else:
            #                 lr = "Right"
            #             displayName = t.displayName + "Port" + lr + str(
            #                 int(100 * (1 - (p.scenePos().y() - p.parent.scenePos().y()) / p.parent.h)))
            #             for
            #
            #             if p.name == 'i':
            #                 connectionDict[displayName] = [t.trnsysId,p.connectionList[0].toPortId, p.connectionList[0].toPortId]
            #             elif p.name == 'o':
            #                 connectionDict[displayName] = [t.trnsysId, p.connectionList[0].toPortId,p.connectionList[0].toPortId]
            if not isinstance(t, StorageTank):
                toElement = ''
                try:
                    toElement = t.toPort.parent.trnsysId
                except:
                    pass

                fromElement = ''
                try:
                    fromElement = t.fromPort.parent.trnsysId
                except:
                    pass

                connectionDict[t.displayName] =  [t.trnsysId,toElement,fromElement]
                connectionDictNum[str(t.trnsysId)] = t.displayName
        return connectionDict, connectionDictNum

    def exportBlackBox(self,exportTo='ddck'):
        f = "*** Black box component temperatures" + "\n"
        equationNr = 0
        problemEncountered = False

        for t in self.trnsysObj:
            status, equations = t.exportBlackBox()
            if status == 'success':
                for equation in equations:
                    f += equation + "\n"
                equationNr += len(equations)
            elif status == 'noDdckFile' or status == 'noDdckEntry':
                problemEncountered = True
                if status == 'noDdckFile':
                    messageText = 'No ddck-file was found in the folder of ' + t.displayName + '.'
                elif status == 'noDdckEntry':
                    messageText = 'No output temperature entry was found in the ddck-file(s) of ' + t.displayName + '.'
                messageText = messageText + ' This issue needs to be addressed before a file can be exported.'
                qmb = QMessageBox()
                qmb.setText(messageText)
                qmb.setStandardButtons(QMessageBox.Ok)
                qmb.setDefaultButton(QMessageBox.Ok)
                qmb.exec()
                break

        if exportTo == 'mfs':
            lines = f.split("\n")
            f = ''
            for i in range(len(lines)):
                if "=" in lines[i]:
                    lines[i] = lines[i].split("=")[0] + "=1"
                f += lines[i] + "\n"

        f = "\nEQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return problemEncountered,f

    def exportPumpOutlets(self):
        f = "*** Pump outlet temperatures" + "\n"
        equationNr = 0
        for t in self.trnsysObj:
            f += t.exportPumpOutlets()[0]
            equationNr += t.exportPumpOutlets()[1]

        f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"
        return f

    def exportMassFlows(self): # What the controller should give
        f = "*** Massflowrates" + "\n"
        equationNr = 0

        for t in self.trnsysObj:
            f += t.exportMassFlows()[0]
            equationNr += t.exportMassFlows()[1]

        f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return f

    def exportDivSetting(self, unit, exportTo='hydraulics'):
        """

        :param unit: the index of the previous unit number used.
        :return:
        """
        canceled = False
        if exportTo == 'hydraulics':
            ddckPath = os.path.join(self.editor.projectFolder,'ddck\\control')
            if os.path.isfile(ddckPath + '\\valve_control.ddck'):
                qmb = QMessageBox()
                qmb.setText("Warning: " +
                            "The file control\\valve_control.ddck already exists. Do you want to overwrite it or cancel?")
                qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                qmb.setDefaultButton(QMessageBox.Cancel)
                ret = qmb.exec()
                if ret == QMessageBox.Cancel:
                    canceled = True

        f = ''

        if not canceled:
            nUnit = unit
            constants = 0
            f2 = ''
            for t in self.trnsysObj:
                f2 += t.exportDivSetting1()[0]
                constants += t.exportDivSetting1()[1]

            if constants > 0:
                f = "CONSTANTS " + str(constants) + "\n"
                f += f2 + "\n"

            for t in self.trnsysObj:
                res = t.exportDivSetting2(nUnit)
                f += res[0]
                nUnit = res[1]

            if f != '' and exportTo == 'hydraulics':
                header = "*************************************\n"
                header += "**BEGIN valve_control.ddck\n"
                header += "*************************************\n\n"
                f = header + f

                outfile = open(ddckPath + '\\valve_control.ddck', 'w')
                outfile.writelines(f)
                outfile.close()

        return canceled, f

    def exportParametersFlowSolver(self, simulationUnit, simulationType, descConnLength):
        # If not all ports of an object are connected, less than 4 numbers will show up
        # TrnsysConn is a list containing the fromPort and twoPort in order as they appear in the export of connections
        f = ""
        f += "UNIT " + str(simulationUnit) + " TYPE " + str(simulationType) + "\n"
        f += "PARAMETERS " + str(self.numOfPar) + "\n"
        f += str(self.lineNumOfPar) + "\n"

        # exportConnsString: i/o i/o 0 0
        tempObjList = []
        nameString = ''
        for t in self.trnsysObj:

            noHydraulicConnection = isinstance(t,StorageTank) or (not(isinstance(t, Connection)) and not t.outputs and not t.inputs)

            if noHydraulicConnection:
                continue
            else:
                ObjToCheck = t.exportParametersFlowSolver(descConnLength)[0]
                f += ObjToCheck
                ObjToCheck = str(ObjToCheck).split(': ')[-1].rstrip()

            # f += t.exportParametersFlowSolver(descConnLength)[0]

            # if ObjToCheck in tempObjList and ObjToCheck != '\n' and ObjToCheck != '' and ObjToCheck != ' ':
            #     msgBox = QMessageBox()
            #     msgBox.setText("Variable name <b>%s</b> already exists! Please try again after renaming." % ObjToCheck)
            #     msgBox.exec_()
            #     # return False
            # else:
            #     tempObjList.append(ObjToCheck)

                if len(ObjToCheck) > self.maxChar-5:
                    nameString += ObjToCheck + '\n'
                # return False

            # print(ObjToCheck)
            # print(len(ObjToCheck))
        if nameString != '':
            msgBox = QMessageBox()
            msgBox.setText(
                "The following variable names :\n%shas longer than %d characters!" % (nameString, self.maxChar - 5))
            msgBox.exec_()

        tempS = f
        print("param solver text is ")
        print(f)
        t = self.convertToStringList(tempS)
        print("And now the ids come")

        f = "\n".join(t[0:3]) + "\n" + self.correctIds(t[3:]) + "\n"

        return f

    def convertToStringList(self, l):
        res = []
        temp = ""
        for i in l:
            if i == "\n":
                res.append(temp)
                temp = ""
            else:
                temp += i

        return res

    def findId(self, s):
        a = s[s.find("!") + 1:s.find(" ", s.find("!"))]
        print(a)
        return a

    def correctIds(self, lineList):
        fileCopy = lineList[:]
        print("fds" + str(fileCopy))
        fileCopy = [" " + l for l in fileCopy]

        matchNumber = re.compile(r'\d+')

        counter = 0
        for line in lineList:
            counter += 1
            k = self.findId(line)
            if k != str(counter):

                descConnlen = 15
                res = fileCopy[:]
                for l in range(len(fileCopy)):
                    # print("In filecopy...")
                    ids = matchNumber.findall(fileCopy[l])
                    # print("ids are " + str(ids) + " k is " + str(k))
                    # print(res[l])
                    for i in range(3):
                        if ids[i] == str(k):
                            ids[i] = str(counter)

                    fileCopyTempLine = fileCopy[l]
                    rest = fileCopyTempLine[fileCopyTempLine.find("!"):]
                    res[l] = ids[0] + " " + ids[1] + " " + ids[2] + " " + ids[3]
                    res[l] += " "*(descConnlen - len(res[l])) + rest
                    # print(res[l])

                fileCopy = res
                fileCopy = [l.replace("!" + str(k) + " ", "!" + str(counter) + " ") for l in fileCopy]

                # fileCopy = [l.replace(" " + str(k) + " ", " " + str(counter) + " ") for l in fileCopy]
                # fileCopy = [l.replace("!" + str(k) + " ", "!" + str(counter) + " ") for l in fileCopy]

        # fileCopy = [l[1:None] for l in fileCopy]
        return '\n'.join(fileCopy)

    def exportInputsFlowSolver(self):
        #  add a string to block and connection for exportPrintInput
        f = ''
        f += "INPUTS " + str(self.lineNumOfPar) + "! for Type 935\n"

        counter = 0

        for t in self.trnsysObj:
            # if type(t) is StorageTank:
            #     continue
            # if type(t) is Connection and (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
            #     continue
            #
            # if t.typeNumber in [1, 4]:
            #     temp1 = pump_prefix + t.displayName
            #     t.exportInputName = " " + temp1 + " "
            #     temp += t.exportInputName
            #     t.exportInitialInput = 0.0
            # elif t.typeNumber == 3:
            #     temp1 = mix_prefix + t.displayName
            #     t.exportInputName = " " + temp1 + " "
            #     temp += t.exportInputName
            #     t.exportInitialInput = 0.0
            # else:
            #     temp += " 0,0 "
            #     # Because a HeatPump appears twice in the hydraulic export
            #     # Same for the generic block
            #     if type(t) is HeatPump:
            #         temp += " 0,0 "
            #         counter += 1
            #     if type(t) is GenericBlock:
            #         for i in range(len(t.inputs)-1):
            #             temp += " 0,0 "
            #             counter += 1
            res = t.exportInputsFlowSolver1()
            f += res[0]
            counter += res[1]

            if counter > 8 or t == self.trnsysObj[-1]:
                f += "\n"
                counter = 0

        f += "\n*** Initial Inputs *" + "\n"

        counter2 = 0
        for t in self.trnsysObj:
            # if type(t) is StorageTank:
            #     continue
            # if type(t) is Connection and (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
            #     continue
            # if type(t) is HeatPump:
            #     # 100120 Why only one exportInitialInput for Heatpump? => what for Generic Block
            #     f += " " + str(t.exportInitialInput) + " " + str(t.exportInitialInput) + " "
            #     f += " " + str(t.exportInitialInput) + " " + str(t.exportInitialInput) + " "
            #     counter2 += 1
            #     continue
            #
            # if type(t) is GenericBlock:
            #     for i in range(len(t.inputs)):
            #         f += " " + str(t.exportInitialInput) + " " + str(t.exportInitialInput) + " "
            #         counter2 += 1
            #     continue
            res = t.exportInputsFlowSolver2()
            f += res[0]
            counter2 += res[1]

            if counter2 > 8:
                f += "\n"
                counter2 = 0

        f += "\n\n"

        return f

    def exportOutputsFlowSolver(self, simulationUnit):
        f = ''

        abc = list(string.ascii_uppercase)[0:3]

        prefix = "Mfr"
        equationNumber = 1
        nEqUsed = 1 # DC

        tot = ""

        # counter = 1
        for t in self.trnsysObj:
            # for i in range(0, (1 + int((t.typeNumber == 2) or (t.typeNumber == 3))))
            # if type(t) is StorageTank:
            #     continue
            # if type(t) is Connection and (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank):
            #     continue
            # #if type(t) is GenericBlock:
            #     # pass
            # if type(t) is HeatPump:
            #     for i in range(0, 3):
            #
            #         if i < 2:
            #             temp = prefix + t.displayName + "-HeatPump" + "_" + abc[i] + "=[" + str(simulationUnit) + "," +\
            #                    str(equationNumber) + "]\n"
            #             tot += temp
            #             t.exportEquations.append(temp)
            #             nEqUsed += 1 #DC
            #         equationNumber += 1 #DC-ERROR it should count anyway
            #
            #     for i in range(0, 3):
            #
            #         if i < 2:
            #             temp = prefix + t.displayName + "_Evap" + "_" + abc[i] + "=[" + \
            #                    str(simulationUnit) + "," + str(equationNumber) + "]\n"
            #             tot += temp
            #             t.exportEquations.append(temp)
            #             nEqUsed += 1 #DC
            #         equationNumber += 1 #DC-ERROR it should count anyway
            #     continue
            #
            # for i in range(0, 3):
            #     if t.typeNumber == 2 or t.typeNumber == 3:
            #         if(t.isVisible()):
            #             temp = prefix + t.displayName + "_" + abc[i] + "=[" + str(simulationUnit) + "," + \
            #                    str(equationNumber) + "]\n"
            #             tot += temp
            #             t.exportEquations.append(temp)
            #             nEqUsed += 1 #DC
            #
            #         equationNumber += 1 #DC-ERROR this needs to add even of is virtual. We don't print it but it exist in the flow solver
            #
            #     else:
            #         if i < 2:
            #             temp = prefix + t.displayName + "_" + abc[i] + "=[" + str(simulationUnit) + "," + \
            #                    str(equationNumber) + "]\n"
            #             tot += temp
            #             t.exportEquations.append(temp)
            #             nEqUsed += 1 #DC
            #         equationNumber += 1#DC-ERROR it should count anyway
            noHydraulicConnection = isinstance(t, StorageTank) or (not (isinstance(t, Connection)) and not t.outputs and not t.inputs)

            if noHydraulicConnection:
                continue
            else:
                res = t.exportOutputsFlowSolver(prefix, abc, equationNumber, simulationUnit)
                tot += res[0]
                equationNumber = res[1]
                nEqUsed += res[2]

        head = "EQUATIONS {0}	! Output up to three (A,B,C) mass flow rates of each component, positive = " \
               "input/inlet, negative = output/outlet ".format(nEqUsed-1)

        f += head + "\n"
        f += tot + "\n"
        f += "\n"

        return f

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        # Prints the part of the export where the pipes, tp and div Units are printed

        f = ''
        unitNumber = startingUnit
        # typeNr1 = 929 # Temperature calculation from a tee-piece
        # typeNr2 = 931 # Temperature calculation from a pipe

        for t in self.trnsysObj:

            # unitText = ""
            # ambientT = 20
            #
            # densityVar = "RhoWat"
            # specHeatVar = "CPWat"
            #
            # equationConstant1 = 1
            # equationConstant2 = 3
            #
            # # T-Pieces and Mixers
            # if (t.typeNumber == 2 or t.typeNumber == 3) and t.isVisible():  # DC-ERROR added isVisible
            #     unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr1) + "\n"
            #     unitText += "!" + t.displayName + "\n"
            #     unitText += "PARAMETERS 0\n"
            #     unitText += "INPUTS 6\n"
            #
            #     for s in t.exportEquations:
            #         unitText += s[0:s.find('=')] + "\n"
            #
            #     for it in t.trnsysConn:
            #         unitText += "T" + it.displayName + "\n"
            #
            #     unitText += "***Initial values\n"
            #     unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"
            #
            #     unitText += "EQUATIONS 1\n"
            #     unitText += "T" + t.displayName + "= [" + str(unitNumber) + "," + str(equationConstant1) + "]\n"
            #
            #     unitNumber += 1
            #     f += unitText + "\n"
            #
            # # Pipes DC-ERROR added isVisible below. The fromPort toPort StorageTank does not work to detect if it is virtual.
            # if type(t) is Connection and not (type(t.fromPort.parent) is StorageTank or type(t.toPort.parent) is StorageTank) and not t.hiddenGenerated:
            # # if type(t) is Connection and t.firstS.isVisible:
            #     # if t.isVirtualConn and t.isStorageIO:
            #     # DC-ERROR Connections don't have isVisble(), but we need to avoid printing the virtual ones here
            #     # if t.firstS.isVisible(): #DC-ERROR still not working. Adding the isVisble also ignores (besides the virtaul ones) those pipes connected to the TEs t.isVisible():
            #     if True:
            #         parameterNumber = 6
            #         inputNumbers = 4
            #
            #         # Fixed strings
            #         diameterPrefix = "di"
            #         lengthPrefix = "L"
            #         lossPrefix = "U"
            #         tempRoomVar = "TRoomStore"
            #         initialValueS = "20 0.0 20 20"
            #         powerPrefix = "P"
            #
            #         # Momentarily hardcoded
            #         equationNr = 3
            #
            #         unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
            #         unitText += "!" + t.displayName + "\n"
            #         unitText += "PARAMETERS " + str(parameterNumber) + "\n"
            #
            #         unitText += diameterPrefix + t.displayName + "\n"
            #         unitText += lengthPrefix + t.displayName + "\n"
            #         unitText += lossPrefix + t.displayName + "\n"
            #         unitText += densityVar + "\n"
            #         unitText += specHeatVar + "\n"
            #         unitText += str(ambientT) + "\n"
            #
            #         unitText += "INPUTS " + str(inputNumbers) + "\n"
            #
            #         if len(t.trnsysConn) == 2:
            #             # if isinstance(Connector, t.trnsysConn[0]) and not t.trnsysConn[0].isVisible() and firstGenerated:
            #             # or if it is tpiece and not visible and firstGenerated
            #             if isinstance(t.trnsysConn[0], BlockItem) and not t.trnsysConn[0].isVisible():
            #                 # This is the case for a generated TPiece
            #                 portToPrint = None
            #                 for p in t.trnsysConn[0].inputs + t.trnsysConn[0].outputs:
            #                     if t in p.connectionList:
            #                         # Found the port of the generated block adjacent to this pipe
            #                         # Assumes 1st connection is with storageTank
            #                         if t.fromPort == p:
            #                             if t.toPort.connectionList[0].fromPort == t.toPort:
            #                                 portToPrint = t.toPort.connectionList[0].toPort
            #                             else:
            #                                 portToPrint = t.toPort.connectionList[0].fromPort
            #                         else:
            #                             if t.fromPort.connectionList[0].fromPort == t.fromPort:
            #                                 portToPrint = t.fromPort.connectionList[0].toPort
            #                             else:
            #                                 portToPrint = t.fromPort.connectionList[0].fromPort
            #                 if portToPrint is None:
            #                     print("Error: No portToprint found when printing UNIT of " + t.displayName)
            #                     return
            #
            #                 if portToPrint.side == 0:
            #                     lr = "Left"
            #                 else:
            #                     lr = "Right"
            #
            #                 unitText += "T" + portToPrint.parent.displayName + "Port" + lr + str(int(100 * (1 - (
            #                             portToPrint.scenePos().y() - portToPrint.parent.scenePos().y()) / portToPrint.parent.h))) + "\n"
            #             else:
            #                 unitText += "T" + t.trnsysConn[0].displayName + "\n"
            #
            #             unitText += t.exportEquations[0][0:t.exportEquations[0].find("=")] + "\n"
            #             unitText += tempRoomVar + "\n"
            #
            #             if isinstance(t.trnsysConn[1], BlockItem) and not t.trnsysConn[1].isVisible():
            #                 portToPrint = None
            #                 for p in t.trnsysConn[1].inputs + t.trnsysConn[1].outputs:
            #                     if t in p.connectionList:
            #                         # Found the port of the generated block adjacent to this pipe
            #                         # Assumes 1st connection is with storageTank
            #                         if t.fromPort == p:
            #                             if t.toPort.connectionList[0].fromPort == t.toPort:
            #                                 portToPrint = t.toPort.connectionList[0].toPort
            #                             else:
            #                                 portToPrint = t.toPort.connectionList[0].fromPort
            #                         else:
            #                             if t.fromPort.connectionList[0].fromPort == t.fromPort:
            #                                 portToPrint = t.fromPort.connectionList[0].toPort
            #                             else:
            #                                 portToPrint = t.fromPort.connectionList[0].fromPort
            #
            #                 if portToPrint is None:
            #                     print("Error: No portToprint found when printing UNIT of " + t.displayName)
            #                     return
            #
            #                 if portToPrint.side == 0:
            #                     lr = "Left"
            #                 else:
            #                     lr = "Right"
            #
            #                 unitText += "T" + portToPrint.parent.displayName + "Port" + lr + str(int(100 * (1 - (
            #                         portToPrint.scenePos().y() - portToPrint.parent.scenePos().y()) / portToPrint.parent.h))) + "\n"
            #             else:
            #                 unitText += "T" + t.trnsysConn[1].displayName + "\n"
            #
            #             # unitText += "T" + t.trnsysConn[0].displayName + "\n"
            #             # unitText += t.exportEquations[0][0:t.exportEquations[0].find("=")] + "\n"
            #             # unitText += tempRoomVar + "\n"
            #             # unitText += "T" + t.trnsysConn[1].displayName + "\n"
            #         else:
            #             f += "Error: NO VALUE\n" * 3 + "at connection with parents " + str(t.fromPort.parent) + str(t.toPort.parent) + "\n"
            #
            #         unitText += "***Initial values\n"
            #         unitText += initialValueS + "\n\n"
            #
            #         unitText += "EQUATIONS " + str(equationNr) + "\n"
            #         unitText += "T" + t.displayName + "= [" + str(unitNumber) + "," + str(equationConstant1) + "]\n"
            #         unitText += powerPrefix + t.displayName + "_kW" + "= [" + str(unitNumber) + "," + str(
            #             equationConstant2) + "]/3600 !kW\n"
            #         unitText += "Mfr" + t.displayName + "= " + "Mfr" + t.displayName + "_A" "\n"
            #
            #         unitNumber += 1
            #         unitText += "\n"
            #         f += unitText
            #     else:
            #         pass # virtual element
            res = t.exportPipeAndTeeTypesForTemp(unitNumber)
            f += res[0]
            unitNumber = res[1]

        self.editor.printerUnitnr = unitNumber

        return f

    def exportPrintLoops(self):
        f = ''
        loopText = ''
        constsNr = 0
        constString = "CONSTANTS "
        suffix1 = "_save"
        string1 = "dtSim/rhoWat/"
        Pi = "3.14"
        for g in self.editor.groupList:

            loopText += "** Fluid Loop : " + g.displayName + "\n"

            loopNr = self.editor.groupList.index(g)

            diLp = "di_loop_" + str(loopNr)
            LLp = "L_loop_" + str(loopNr)
            ULp = "U_loop_" + str(loopNr)

            loopText += diLp + "=" + str(g.exportDi) + "\n"
            loopText += LLp + "=" + str(g.exportL) + "\n"
            loopText += ULp + "=" + str(g.exportU) + "\n"
            # loopText += LLp + suffix1 + " = " "Mfr_" + "loop_" + str(loopNr) + "_nom*" + string1 + "((" + \
            #             diLp + "/2)^2*" + Pi + ")\n"

            # loopText += ULp + suffix1 + " = " + str(g.exportU) + "*" + LLp + suffix1

            constsNr += 3

            loopText += "\n"

        f += constString + str(constsNr) + "\n"
        f += loopText + "\n"

        return f

    def exportPrintPipeLoops(self):
        f = ''
        loopText = ""
        equationString = "EQUATIONS "
        equationNr = 0

        for g in self.editor.groupList:
            loopText += "** Fluid Loop : " + g.displayName + "\n"

            loopNr = self.editor.groupList.index(g)

            diLp = "di_loop_" + str(loopNr)
            LLp = "L_loop_" + str(loopNr)
            ULp = "U_loop_" + str(loopNr)

            loopText += "**" + diLp + "=" + str(g.exportDi) + "\n"
            loopText += "**" + LLp + "=" + str(g.exportL) + "\n"
            loopText += "**" + ULp + "=" + str(g.exportU) + "\n"

            for c in g.itemList:
                if isinstance(c, Connection) and not c.isVirtualConn:
                    loopText += "*** " + c.displayName + "\n"
                    loopText += "di" + c.displayName + "=" + diLp + "\n"
                    loopText += "L" + c.displayName + "=" + LLp + "\n"
                    loopText += "U" + c.displayName + "=" + ULp + "\n"
                    equationNr += 3

            loopText += "\n"

        f += equationString + str(equationNr) + "\n"
        f += loopText + "\n"
        return f

    def exportPrintPipeLosses(self):
        f = ''
        lossText = ''
        strVar = 'PipeLoss'
        totalLeftText = strVar + "Total="
        totalRightText = ''
        equationCounter = 0

        for g in self.editor.groupList:
            leftText = strVar + str(self.editor.groupList.index(g)) + "="
            rightText = ''
            rightCounter = 0

            for i in g.itemList:
                if isinstance(i, Connection) and not i.isVirtualConn:
                    rightText += "P" + i.displayName + "_kW" + "+"
                    rightCounter += 1

            if rightCounter > 0:
                rightText = rightText[:-1]
                lossText += leftText + rightText + '\n'
                totalRightText += strVar + str(self.editor.groupList.index(g)) + "+"
                equationCounter += 1

        totalRightText = totalRightText[:-1]

        f += "EQUATIONS " + str(equationCounter + 1) + "\n" + lossText + totalLeftText + totalRightText +  "\n\n"
        return f

    def exportMassFlowPrinter(self, unitnr, descLen):
        typenr = 25
        printingMode = 0
        relAbsStart = 0
        overwriteApp = -1
        printHeader = -1
        delimiter = 0
        printLabels = 1

        f = "ASSIGN " + self.editor.diagramName.split('.')[0] + "_Mfr.prt " + str(unitnr) + "\n\n"

        f += "UNIT " + str(unitnr) + " TYPE " + str(typenr)
        f += " " * (descLen - len(f)) + "! User defined Printer" + "\n"
        f += "PARAMETERS 10" + "\n"
        f += "dtSim"
        f += " " * (descLen - len(f)) + "! 1 Printing interval" + "\n"
        f += "START"
        f += " " * (descLen - len(f)) + "! 2 Start time" + "\n"
        f += "STOP"
        f += " " * (descLen - len(f)) + "! 3 Stop time" + "\n"
        f += str(unitnr)
        f += " " * (descLen - len(f)) + "! 4 Logical unit" + "\n"
        f += str(printingMode)
        f += " " * (descLen - len(f)) + "! 5 Units printing mode" + "\n"
        f += str(relAbsStart)
        f += " " * (descLen - len(f)) + "! 6 Relative or absolute start time" + "\n"
        f += str(overwriteApp)
        f += " " * (descLen - len(f)) + "! 7 Overwrite or Append" + "\n"
        f += str(printHeader)
        f += " " * (descLen - len(f)) + "! 8 Print header" + "\n"
        f += str(delimiter)
        f += " " * (descLen - len(f)) + "! 9 Delimiter" + "\n"
        f += str(printLabels)
        f += " " * (descLen - len(f)) + "! 10 Print labels" + "\n"
        f += "\n"

        s = ''
        breakline = 0
        for t in self.trnsysObj:
            if isinstance(t, Connection) and not t.isVirtualConn:
                breakline += 1
                if breakline % 8 == 0:
                    s += "\n"
                s += "Mfr" + t.displayName + " "
            if isinstance(t, TVentil) and t.isVisible():
                breakline += 1
                if breakline % 8 == 0:
                    s += "\n"
                s += "xFrac" + t.displayName + " "
        f += "INPUTS " + str(breakline) + "\n" + s + "\n" + "***" + "\n" + s + "\n\n"

        return f

    def exportTempPrinter(self, unitnr, descLen):

        typenr = 25
        printingMode = 0
        relAbsStart = 0
        overwriteApp = -1
        printHeader = -1
        delimiter = 0
        printLabels = 1

        f = "ASSIGN " + self.editor.diagramName.split('.')[0] + "_T.prt " + str(unitnr) + "\n\n"

        f += "UNIT " + str(unitnr) + " TYPE " + str(typenr)
        f += " " * (descLen - len(f)) + "! User defined Printer" + "\n"
        f += "PARAMETERS 10" + "\n"
        f += "dtSim"
        f += " " * (descLen - len(f)) + "! 1 Printing interval" + "\n"
        f += "START"
        f += " " * (descLen - len(f)) + "! 2 Start time" + "\n"
        f += "STOP"
        f += " " * (descLen - len(f)) + "! 3 Stop time" + "\n"
        f += str(unitnr)
        f += " " * (descLen - len(f)) + "! 4 Logical unit" + "\n"
        f += str(printingMode)
        f += " " * (descLen - len(f)) + "! 5 Units printing mode" + "\n"
        f += str(relAbsStart)
        f += " " * (descLen - len(f)) + "! 6 Relative or absolute start time" + "\n"
        f += str(overwriteApp)
        f += " " * (descLen - len(f)) + "! 7 Overwrite or Append" + "\n"
        f += str(printHeader)
        f += " " * (descLen - len(f)) + "! 8 Print header" + "\n"
        f += str(delimiter)
        f += " " * (descLen - len(f)) + "! 9 Delimiter" + "\n"
        f += str(printLabels)
        f += " " * (descLen - len(f)) + "! 10 Print labels" + "\n"
        f += "\n"

        s = ''
        breakline = 0
        for t in self.trnsysObj:
            if isinstance(t, Connection) and not t.isVirtualConn:
                breakline += 1
                if breakline % 8 == 0:
                    s += "\n"
                s += "T" + t.displayName + " "
        f += "INPUTS " + str(breakline) + "\n" + s + "\n" + "***" + "\n" + s + "\n\n"

        return f






