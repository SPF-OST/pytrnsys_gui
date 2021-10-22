# pylint: skip-file
# type: ignore

import glob
import os

import massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem
from massFlowSolver import InternalPiping
from trnsysGUI.SinglePipePortItem import SinglePipePortItem


class BlockItemFourPorts(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(BlockItemFourPorts, self).__init__(trnsysType, parent, **kwargs)

        self.logger = parent.logger

        self.h = 120
        self.w = 120
        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.inputs.append(SinglePipePortItem("i", 2, self))
        self.outputs.append(SinglePipePortItem("o", 0, self))
        self.outputs.append(SinglePipePortItem("o", 2, self))

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

    def getInternalPiping(self) -> InternalPiping:
        side1Input = _mfn.PortItem()
        side1Output = _mfn.PortItem()
        side1Pipe = _mfn.Pipe(f"{self.displayName}Side1", self.childIds[0], side1Input, side1Output)

        side2Input = _mfn.PortItem()
        side2Output = _mfn.PortItem()
        side2Pipe = _mfn.Pipe(f"{self.displayName}Side2", self.childIds[1], side2Input, side2Output)

        modelPortItemsToGraphicalPortItem = {
            side1Input: self.inputs[0],
            side1Output: self.outputs[0],
            side2Input: self.inputs[1],
            side2Output: self.outputs[1]
        }

        return InternalPiping([side1Pipe, side2Pipe], modelPortItemsToGraphicalPortItem)

    def getSubBlockOffset(self, c):
        for i in range(2):
            if (
                self.inputs[i] == c.toPort
                or self.inputs[i] == c.fromPort
                or self.outputs[i] == c.toPort
                or self.outputs[i] == c.fromPort
            ):
                return i
