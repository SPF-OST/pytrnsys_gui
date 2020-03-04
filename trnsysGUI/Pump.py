from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QIcon

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class Pump(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(Pump, self).__init__(trnsysType, parent, **kwargs)
        # factor = 0.6 for old pump
        # factor = 0.5
        # self.w = 100 * factor
        # self.h = 100 * factor
        self.w = 30
        self.h = 30
        self.typeNumber = 1

        self.exportInitialInput = 0.0

        self.inputs.append(PortItem('i', 0, self))
        self.outputs.append(PortItem('o', 2, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

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

        # Update port positions:
        self.inputs[0].setPos(self.flippedH * w - 2* delta + 2 * delta * self.flippedH, h / 2)
        self.outputs[0].setPos(w - self.flippedH * w - 2* delta * self.flippedH, h / 2)
        # self.outputs[0].setPos(w - self.flippedH * w - 2 * delta * self.flippedH + 2 * delta, h / 2)
        # self.inputs[0].side = 2 * self.flippedH
        # self.outputs[0].side = 2 - 2 * self.flippedH
        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        return w, h

    def exportBlackBox(self):
        return "", 0

    def exportPumpOutlets(self):
        f = "T" + self.displayName + " = " + "T" + self.inputs[0].connectionList[0].displayName + "\n"
        equationNr = 1
        return f, equationNr

    def exportMassFlows(self):
        resStr = "Mfr" + self.displayName + " = 1000" + "\n"
        equationNr = 1
        return resStr, equationNr

    def exportInputsFlowSolver1(self):
        temp1 = "Mfr" + self.displayName
        self.exportInputName = " " + temp1 + " "
        return self.exportInputName, 1


