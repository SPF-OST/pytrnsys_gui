# pylint: skip-file
# type: ignore

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
        self.logger = editor.logger

        self.trnsysObj = objList
        self.editor = editor
        self.maxChar = 20

        self.lineNumOfPar = 0
        for component in self.trnsysObj:
            if isinstance(component, Connection):
                numOfRelPorts = 1
            else:
                numOutputs = len(component.outputs)
                numInputs = len(component.inputs)

                if (numInputs == 0 and numOutputs == 1) or (numInputs == 1 and numOutputs == 0):
                    numOfRelPorts = 1
                else:
                    numOfRelPorts = min(numOutputs, numInputs)
            self.lineNumOfPar += numOfRelPorts
        self.numOfPar = 4 * self.lineNumOfPar + 1

    def exportBlackBox(self, exportTo="ddck"):
        f = "*** Black box component temperatures" + "\n"
        equationNr = 0
        problemEncountered = False

        for t in self.trnsysObj:
            status, equations = t.exportBlackBox()

            for equation in equations:
                f += equation + "\n"
            equationNr += len(equations)

        if exportTo == "mfs":
            lines = f.split("\n")
            f = ""
            for i in range(len(lines)):
                if "=" in lines[i]:
                    lines[i] = lines[i].split("=")[0] + "=1"
                f += lines[i] + "\n"

        f = "\nEQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return problemEncountered, f

    def exportPumpOutlets(self):
        f = "*** Pump outlet temperatures" + "\n"
        equationNr = 0
        for t in self.trnsysObj:
            f += t.exportPumpOutlets()[0]
            equationNr += t.exportPumpOutlets()[1]

        f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"
        return f

    def exportMassFlows(self):  # What the controller should give
        f = "*** Massflowrates" + "\n"
        equationNr = 0

        for t in self.trnsysObj:
            f += t.exportMassFlows()[0]
            equationNr += t.exportMassFlows()[1]

        f = "EQUATIONS " + str(equationNr) + "\n" + f + "\n"

        return f

    def exportDivSetting(self, unit):
        """
        :param unit: the index of the previous unit number used.
        :return:
        """
        f = ""

        nUnit = unit
        constants = 0
        f2 = ""
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

        return f

    def exportParametersFlowSolver(self, simulationUnit, simulationType, descConnLength):
        # If not all ports of an object are connected, less than 4 numbers will show up
        # TrnsysConn is a list containing the fromPort and twoPort in order as they appear in the export of connections
        f = ""
        f += "UNIT " + str(simulationUnit) + " TYPE " + str(simulationType) + "\n"
        f += "PARAMETERS " + str(self.numOfPar) + "\n"
        f += str(self.lineNumOfPar) + "\n"

        # exportConnsString: i/o i/o 0 0
        nameString = ""
        for t in self.trnsysObj:

            noHydraulicConnection = not isinstance(t, Connection) and not t.outputs and not t.inputs

            if noHydraulicConnection:
                continue
            else:
                ObjToCheck = t.exportParametersFlowSolver(descConnLength)
                f += ObjToCheck
                ObjToCheck = str(ObjToCheck).split(": ")[-1].rstrip()

                if len(ObjToCheck) > self.maxChar - 5:
                    nameString += ObjToCheck + "\n"

        if nameString != "":
            msgBox = QMessageBox()
            msgBox.setText(
                "The following variable names :\n%shas longer than %d characters!" % (nameString, self.maxChar - 5)
            )
            msgBox.exec_()

        tempS = f
        self.logger.debug("param solver text is ")
        self.logger.debug(f)
        t = self.convertToStringList(tempS)
        self.logger.debug("And now the ids come")

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
        a = s[s.find("!") + 1 : s.find(" ", s.find("!"))]
        self.logger.debug(a)
        return a

    def correctIds(self, lineList):
        fileCopy = lineList[:]
        self.logger.debug("fds" + str(fileCopy))
        fileCopy = [" " + l for l in fileCopy]

        matchNumber = re.compile(r"\d+")

        counter = 0
        for line in lineList:
            counter += 1
            k = self.findId(line)
            if k != str(counter):

                descConnlen = 15
                res = fileCopy[:]
                for l in range(len(fileCopy)):
                    ids = matchNumber.findall(fileCopy[l])
                    for i in range(3):
                        if ids[i] == str(k):
                            ids[i] = str(counter)

                    fileCopyTempLine = fileCopy[l]
                    rest = fileCopyTempLine[fileCopyTempLine.find("!") :]
                    res[l] = ids[0] + " " + ids[1] + " " + ids[2] + " " + ids[3]
                    res[l] += " " * (descConnlen - len(res[l])) + rest

                fileCopy = res
                fileCopy = [l.replace("!" + str(k) + " ", "!" + str(counter) + " ") for l in fileCopy]

        return "\n".join(fileCopy)

    def exportInputsFlowSolver(self):
        f = ""
        f += "INPUTS " + str(self.lineNumOfPar) + "! for Type 935\n"

        counter = 0

        for t in self.trnsysObj:
            res = t.exportInputsFlowSolver1()
            f += res[0]
            counter += res[1]

            if counter > 8 or t == self.trnsysObj[-1]:
                f += "\n"
                counter = 0

        f += "\n*** Initial Inputs *" + "\n"

        counter2 = 0
        for t in self.trnsysObj:
            res = t.exportInputsFlowSolver2()
            f += res[0]
            counter2 += res[1]

            if counter2 > 8:
                f += "\n"
                counter2 = 0

        f += "\n\n"

        return f

    def exportOutputsFlowSolver(self, simulationUnit):
        f = ""

        abc = "ABC"

        prefix = "Mfr"
        equationNumber = 1
        nEqUsed = 1  # DC

        tot = ""

        for t in self.trnsysObj:
            noHydraulicConnection = not isinstance(t, Connection) and not t.outputs and not t.inputs

            if noHydraulicConnection:
                continue
            else:
                res = t.exportOutputsFlowSolver(prefix, abc, equationNumber, simulationUnit)
                tot += res[0]
                equationNumber = res[1]
                nEqUsed += res[2]

        head = (
            "EQUATIONS {0}	! Output up to three (A,B,C) mass flow rates of each component, positive = "
            "input/inlet, negative = output/outlet ".format(nEqUsed - 1)
        )

        f += head + "\n"
        f += tot + "\n"
        f += "\n"

        return f

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        # Prints the part of the export where the pipes, tp and div Units are printed

        f = ""
        unitNumber = startingUnit
        # typeNr1 = 929 # Temperature calculation from a tee-piece
        # typeNr2 = 931 # Temperature calculation from a pipe

        for t in self.trnsysObj:

            res = t.exportPipeAndTeeTypesForTemp(unitNumber)
            f += res[0]
            unitNumber = res[1]

        self.editor.printerUnitnr = unitNumber

        return f

    def exportPrintLoops(self):
        f = ""
        loopText = ""
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
            constsNr += 3
            loopText += "\n"

        f += constString + str(constsNr) + "\n"
        f += loopText + "\n"

        return f

    def exportPrintPipeLoops(self):
        f = ""
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
                if isinstance(c, Connection):
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
        f = ""
        lossText = ""
        rightCounter = 0

        for i in self.editor.groupList[0].itemList:
            if isinstance(i, Connection):
                if rightCounter == 0:
                    lossText += "P" + i.displayName + "_kW"
                else:
                    lossText += "+" + "P" + i.displayName + "_kW"
                rightCounter += 1

        if rightCounter == 0:
            lossText += "0"

        f += "*** Pipe losses\nEQUATIONS 1\nPipeLossTot=" + lossText + "\n\n"
        return f

    def exportMassFlowPrinter(self, unitnr, descLen):
        typenr = 25
        printingMode = 0
        relAbsStart = 0
        overwriteApp = -1
        printHeader = -1
        delimiter = 0
        printLabels = 1

        f = "ASSIGN " + self.editor.diagramName.split(".")[0] + "_Mfr.prt " + str(unitnr) + "\n\n"

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

        s = ""
        breakline = 0
        for t in self.trnsysObj:
            if isinstance(t, Connection):
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

        f = "ASSIGN " + self.editor.diagramName.split(".")[0] + "_T.prt " + str(unitnr) + "\n\n"

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

        s = ""
        breakline = 0
        for t in self.trnsysObj:
            if isinstance(t, Connection):
                breakline += 1
                if breakline % 8 == 0:
                    s += "\n"
                s += "T" + t.displayName + " "
        f += "INPUTS " + str(breakline) + "\n" + s + "\n" + "***" + "\n" + s + "\n\n"

        return f
