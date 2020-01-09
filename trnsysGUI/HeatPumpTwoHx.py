from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class HeatPumpTwoHx(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(HeatPumpTwoHx, self).__init__(trnsysType, parent, **kwargs)

        self.inputs.append(PortItem('i', 0, self))
        self.inputs.append(PortItem('i', 2, self))
        self.inputs.append(PortItem('i', 2, self))

        self.outputs.append(PortItem('o', 0, self))
        self.outputs.append(PortItem('o', 2, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        # For restoring correct order of trnsysObj list
        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 4

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40
        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.inputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, 4 * h / 15 - 4* h / 15 * self.flippedV + 11/16 * h *self.flippedV)
        self.inputs[1].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w, 0.2 * h - 0.2 * h * self.flippedV + 0.8 * h * self.flippedV)
        self.inputs[2].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w, 0.4 * h - 0.4 * h * self.flippedV + 0.6 * h * self.flippedV)
        self.inputs[0].side = 0 + 2 * self.flippedH
        self.inputs[1].side = 2 - 2 * self.flippedH
        self.inputs[2].side = 2 - 2 * self.flippedH

        self.outputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, 2 * h / 3 - 1/3 * h * self.flippedV)
        self.outputs[1].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w, 0.52 * h - 0.04 * h * self.flippedV)
        self.outputs[2].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w, 0.72 * h - 0.44 * h * self.flippedV)
        self.outputs[0].side = 0 + 2 * self.flippedH
        self.outputs[1].side = 2 - 2 * self.flippedH
        self.outputs[2].side = 2 - 2 * self.flippedH

        return w, h

    def encode(self):
        if self.isVisible():
            print("Encoding a HeatPump")

            portListInputs = []
            portListOutputs = []

            for p in self.inputs:
                portListInputs.append(p.id)
            for p in self.outputs:
                portListOutputs.append(p.id)

            dct = {}
            dct['.__HeatPumpTwoDict__'] = True
            dct['HeatPumpName'] = self.name
            dct['HeatPumpDisplayName'] = self.displayName
            dct['PortsIDIn'] = portListInputs
            dct['PortsIDOut'] = portListOutputs
            dct['HeatPumpPosition'] = (float(self.pos().x()), float(self.pos().y()))
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
        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.childIds = i["childIds"]
        self.displayName = i["HeatPumpName"]
        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            print("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            print("Output at heatExchanger")

        self.setPos(float(i["HeatPumpPosition"][0]), float(i["HeatPumpPosition"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        resBlockList.append(self)
