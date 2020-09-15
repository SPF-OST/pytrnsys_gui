from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QTransform

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class BlockItemFourPorts(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(BlockItemFourPorts, self).__init__(trnsysType, parent, **kwargs)
        self.h = 120
        self.w = 120
        self.inputs.append(PortItem('i', 0, self))
        self.inputs.append(PortItem('i', 2, self))
        self.outputs.append(PortItem('o', 0, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self.subBlockCounter = 0

        self.changeSize()

    def encode(self):
        if self.isVisible():
            print("Encoding a %s block" % self.name)

            # childIdList = []

            portListInputs = []
            portListOutputs = []

            for p in self.inputs:
                portListInputs.append(p.id)
            for p in self.outputs:
                portListOutputs.append(p.id)

            dct = {}
            dct['.__BlockDict__'] = True
            dct['BlockName'] = self.name
            dct['BlockDisplayName'] = self.displayName
            dct['PortsIDIn'] = portListInputs
            dct['PortsIDOut'] = portListOutputs
            dct[self.name+'Position'] = (float(self.pos().x()), float(self.pos().y()))
            dct['ID'] = self.id
            dct['trnsysID'] = self.trnsysId
            dct['childIds'] = self.childIds
            dct['FlippedH'] = self.flippedH
            dct['FlippedV'] = self.flippedH
            dct['RotationN'] = self.rotationN
            dct['GroupName'] = self.groupName

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resConnList, resBlockList):
        print("Loading a %s block" % self.name)

        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            print("Input at %s" % self.name)

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            print("Output at %s" % self.name)

        self.setPos(float(i[self.name+"Position"][0]), float(i[self.name+"Position"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        print("Loading a %s block in Decoder" % self.name)

        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            print("Input at %s" % self.name)

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            print("Output at %s" % self.name)

        self.setPos(float(i[self.name + "Position"][0]) + offset_x, float(i[self.name + "Position"][1] + offset_y))
        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        resBlockList.append(self)

    def exportBlackBox(self):
        resStr = "T" + self.displayName + "X0" + "=1 \n"
        resStr += "T" + self.displayName + "X1" + "=1 \n"
        eqNb = 2
        return resStr, eqNb

    def exportParametersFlowSolver(self, descConnLength):
        # descConnLength = 20
        f = ""
        for i in range(len(self.inputs)):
            # ConnectionList lenght should be max offset
            temp = ""
            for c in self.inputs[i].connectionList:
                if hasattr(c.fromPort.parent, self.name) and self.inputs[i].connectionList.index(c) == 0:
                    continue
                elif hasattr(c.toPort.parent, self.name) and self.inputs[i].connectionList.index(c) == 0:
                    continue
                else:
                    if len(self.outputs[i].connectionList) > 0:

                        if i == 0:
                            temp = str(c.trnsysId) + " " + str(
                                self.outputs[i].connectionList[0].trnsysId) + " 0 0 "  # + str(t.childIds[0])
                            temp += " " * (descConnLength - len(temp))

                            # ExternalHx will have a two-liner exportConnString
                            self.exportConnsString += temp + "\n"
                            f += temp + "!" + str(self.childIds[0]) + " : " + self.displayName + "Side1" + "\n"

                        elif i == 1:
                            temp = str(c.trnsysId) + " " + str(
                                self.outputs[i].connectionList[0].trnsysId) + " 0 0 "  # + str(t.childIds[1])
                            temp += " " * (descConnLength - len(temp))

                            # ExternalHx will have a two liner exportConnString
                            self.exportConnsString += temp + "\n"
                            f += temp + "!" + str(self.childIds[1]) + " : " + self.displayName + "Side2" + "\n"
                        else:
                            f += "Error: There are more inputs than trnsysIds" + "\n"

                        # Presumably used only for storing the order of connections
                        self.trnsysConn.append(c)
                        self.trnsysConn.append(self.outputs[i].connectionList[0])

                    else:
                        f += "Output of %s for input[{0}] is not connected " % self.name.format(i)  + "\n"

        return f, 2

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
                    temp = prefix + self.displayName + "-Side" + str(j) + "_" + abc[i] + "=[" + str(simulationUnit) + "," + \
                           str(equationNumber) + "]\n"
                    tot += temp
                    self.exportEquations.append(temp)
                    # nEqUsed += 1  # DC
                equationNumber += 1  # DC-ERROR it should count anyway

        return tot, equationNumber, 4

    def getSubBlockOffset(self, c):
        for i in range(2):
            if self.inputs[i] == c.toPort or self.inputs[i] == c.fromPort or self.outputs[i] == c.toPort or self.outputs[i] == c.fromPort:
                return i
