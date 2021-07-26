# pylint: skip-file
# type: ignore

import glob
import os

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QTransform

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class BlockItemFourPorts(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(BlockItemFourPorts, self).__init__(trnsysType, parent, **kwargs)

        self.logger = parent.logger

        self.h = 120
        self.w = 120
        self.inputs.append(PortItem("i", 0, self))
        self.inputs.append(PortItem("i", 2, self))
        self.outputs.append(PortItem("o", 0, self))
        self.outputs.append(PortItem("o", 2, self))

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self.changeSize()

    def encode(self):
        if self.isVisible():
            self.logger.debug("Encoding a %s block" % self.name)

            # childIdList = []

            portListInputs = []
            portListOutputs = []

            for p in self.inputs:
                portListInputs.append(p.id)
            for p in self.outputs:
                portListOutputs.append(p.id)

            dct = {}
            dct[".__BlockDict__"] = True
            dct["BlockName"] = self.name
            dct["BlockDisplayName"] = self.displayName
            dct["PortsIDIn"] = portListInputs
            dct["PortsIDOut"] = portListOutputs
            dct[self.name + "Position"] = (float(self.pos().x()), float(self.pos().y()))
            dct["ID"] = self.id
            dct["trnsysID"] = self.trnsysId
            dct["childIds"] = self.childIds
            dct["FlippedH"] = self.flippedH
            dct["FlippedV"] = self.flippedH
            dct["RotationN"] = self.rotationN
            dct["GroupName"] = self.groupName

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resBlockList):
        self.logger.debug("Loading a %s block" % self.name)

        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            self.logger.debug("Input at %s" % self.name)

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            self.logger.debug("Output at %s" % self.name)

        self.setPos(float(i[self.name + "Position"][0]), float(i[self.name + "Position"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self.logger.debug("Loading a %s block in Decoder" % self.name)

        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            self.logger.debug("Input at %s" % self.name)

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            self.logger.debug("Output at %s" % self.name)

        self.setPos(float(i[self.name + "Position"][0]) + offset_x, float(i[self.name + "Position"][1] + offset_y))
        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        resBlockList.append(self)

    def exportBlackBox(self):
        equations = []
        files = glob.glob(os.path.join(self.path, "**/*.ddck"), recursive=True)
        if not (files):
            status = "noDdckFile"
        else:
            status = "noDdckEntry"
        lines = []
        for file in files:
            infile = open(file, "r")
            lines += infile.readlines()
        for i in range(len(lines)):
            if "output" in lines[i].lower() and "to" in lines[i].lower() and "hydraulic" in lines[i].lower():
                counter = 1
                for j in range(i, len(lines) - i):
                    if lines[j][0] == "T":
                        outputT = lines[j].split("=")[0].replace(" ", "")
                        equations.append("T" + self.displayName + "X" + str(counter) + "=1 ! suggestion: " + outputT)
                        counter += 1
                    if counter == 3:
                        status = "success"
                        break
                break

        if status == "noDdckFile" or status == "noDdckEntry":
            equations.append("T" + self.displayName + "X1" + "=1")
            equations.append("T" + self.displayName + "X2" + "=1")

        return status, equations

    def exportParametersFlowSolver(self, descConnLength):
        f = ""
        if self.outputs[0].connectionList:
            incomingConnection = self.inputs[0].connectionList[0]
            outgoingConnection = self.outputs[0].connectionList[0]
            temp = (
                    str(incomingConnection.trnsysId) + " " + str(outgoingConnection.trnsysId) + " 0 0 "
            )
            temp += " " * (descConnLength - len(temp))
            self.exportConnsString += temp + "\n"
            f += temp + "!" + str(self.childIds[0]) + " : " + self.displayName + "Side1" + "\n"
            self.trnsysConn.append(incomingConnection)
            self.trnsysConn.append(outgoingConnection)

        if self.outputs[1].connectionList:
            incomingConnection = self.inputs[1].connectionList[0]
            outgoingConnection = self.outputs[1].connectionList[0]
            temp = (
                    str(incomingConnection.trnsysId) + " " + str(outgoingConnection.trnsysId) + " 0 0 "
            )
            temp += " " * (descConnLength - len(temp))
            self.exportConnsString += temp + "\n"
            f += temp + "!" + str(self.childIds[1]) + " : " + self.displayName + "Side2" + "\n"
            self.trnsysConn.append(incomingConnection)
            self.trnsysConn.append(outgoingConnection)

        return f

    def exportInputsFlowSolver1(self):
        return "0,0 0,0 ", 2

    def exportInputsFlowSolver2(self):
        f = ""
        f += " " + str(self.exportInitialInput) + " " + str(self.exportInitialInput) + " "
        return f, 2

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        tot = ""
        for j in range(2):
            for i in range(0, 3):
                if i < 2:
                    temp = (
                        prefix
                        + self.displayName
                        + "-Side"
                        + str(j)
                        + "_"
                        + abc[i]
                        + "=["
                        + str(simulationUnit)
                        + ","
                        + str(equationNumber)
                        + "]\n"
                    )
                    tot += temp
                    self.exportEquations.append(temp)
                    # nEqUsed += 1  # DC
                equationNumber += 1  # DC-ERROR it should count anyway

        return tot, equationNumber, 4

    def getSubBlockOffset(self, c):
        for i in range(2):
            if (
                self.inputs[i] == c.toPort
                or self.inputs[i] == c.fromPort
                or self.outputs[i] == c.toPort
                or self.outputs[i] == c.fromPort
            ):
                return i
