# pylint: disable = invalid-name

import glob
import os

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.massFlowSolver import InternalPiping, MassFlowNetworkContributorMixin


class BlockItemFourPorts(BlockItem, MassFlowNetworkContributorMixin):  # pylint: disable = too-many-instance-attributes
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.logger = parent.logger

        self.h = 120
        self.w = 120
        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", 2, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self.changeSize()

    def encode(self):
        if not self.isVisible():
            return None
        self.logger.debug(f"Encoding a {self.name} block")

        portListInputs = []
        portListOutputs = []

        for inputPort in self.inputs:
            portListInputs.append(inputPort.id)
        for outputPort in self.outputs:
            portListOutputs.append(outputPort.id)

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
        dct["FlippedV"] = self.flippedV
        dct["RotationN"] = self.rotationN

        dictName = "Block-"

        return dictName, dct

    def decode(self, i, resBlockList):

        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x, inputPort in enumerate(self.inputs):
            inputPort.id = i["PortsIDIn"][x]

        for x, outputPort in enumerate(self.outputs):
            outputPort.id = i["PortsIDOut"][x]

        self.setPos(float(i[self.name + "Position"][0]), float(i[self.name + "Position"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]

        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):

        self.changeSize()

        for x, inputPort in enumerate(self.inputs):
            inputPort.id = i["PortsIDIn"][x]

        for x, outputPort in enumerate(self.outputs):
            outputPort.id = i["PortsIDOut"][x]

        self.setPos(float(i[self.name + "Position"][0]) + offset_x, float(i[self.name + "Position"][1] + offset_y))

        resBlockList.append(self)

    def exportBlackBox(self):
        equations = []
        files = glob.glob(os.path.join(self.path, "**/*.ddck"), recursive=True)
        if not files:
            status = "noDdckFile"
        else:
            status = "noDdckEntry"
        lines = []
        for file in files:
            with open(file, "r") as infile:  # pylint: disable = unspecified-encoding
                lines += infile.readlines()
        for i, line in enumerate(lines):
            if "output" in line.lower() and "to" in line.lower() and "hydraulic" in line.lower():
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

        if status in ("noDdckFile", "noDdckEntry"):
            equations.append("T" + self.displayName + "X1" + "=1")
            equations.append("T" + self.displayName + "X2" + "=1")

        return status, equations

    def getInternalPiping(self) -> InternalPiping:
        side1Input = _mfn.PortItem("Side Input 1", _mfn.PortItemType.INPUT)
        side1Output = _mfn.PortItem("Side Output 1", _mfn.PortItemType.OUTPUT)
        side1Pipe = _mfn.Pipe(f"{self.displayName}Side1", self.childIds[0], side1Input, side1Output)

        side2Input = _mfn.PortItem("Side Input 2", _mfn.PortItemType.INPUT)
        side2Output = _mfn.PortItem("Side Output 2", _mfn.PortItemType.OUTPUT)
        side2Pipe = _mfn.Pipe(f"{self.displayName}Side2", self.childIds[1], side2Input, side2Output)

        modelPortItemsToGraphicalPortItem = {
            side1Input: self.inputs[0],
            side1Output: self.outputs[0],
            side2Input: self.inputs[1],
            side2Output: self.outputs[1]
        }

        return InternalPiping([side1Pipe, side2Pipe], modelPortItemsToGraphicalPortItem)

    def getSubBlockOffset(self, c):  # pylint: disable = invalid-name
        for i in range(2):
            if (
                    self.inputs[i] == c.toPort
                    or self.inputs[i] == c.fromPort
                    or self.outputs[i] == c.toPort
                    or self.outputs[i] == c.fromPort
            ):
                return i
        return None
