from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem


class WTap(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(WTap, self).__init__(trnsysType, parent, **kwargs)
        self.w = 40
        self.h = 40
        self.inputs.append(PortItem('i', 0, self))

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.typeNumber = 5

        self.changeSize()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 20
        deltaHF = 0.45

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

        self.inputs[0].setPos(0,delta)
        # self.inputs[0].side = 0 + 2 * self.flippedH
        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4

        return w, h

    def exportPumpOutlets(self):
        resStr = "T" + self.displayName + " = " + "T" + self.inputs[0].connectionList[0].displayName + "\n"
        equationNr = 1
        return resStr, equationNr

    def exportParametersFlowSolver(self, descConnLength):
        # descConnLength = 20
        temp = ""
        for i in self.inputs:
            # ConnectionList lenght should be max offset
            for c in i.connectionList:
                if hasattr(c.fromPort.parent, "heatExchangers") and i.connectionList.index(c) == 0:
                    continue
                elif hasattr(c.toPort.parent, "heatExchangers") and i.connectionList.index(c) == 0:
                    continue
                else:
                    temp = temp + str(c.trnsysId) + " "
                    self.trnsysConn.append(c)

        for o in self.outputs:
            # ConnectionList lenght should be max offset
            for c in o.connectionList:
                if hasattr(c.fromPort.parent, "heatExchangers") and o.connectionList.index(c) == 0:
                    continue
                elif hasattr(c.toPort.parent, "heatExchangers") and o.connectionList.index(c) == 0:
                    continue
                else:
                    temp = temp + str(c.trnsysId) + " "
                    self.trnsysConn.append(c)

        temp += "0 0 "
        temp += str(self.typeNumber)
        temp += " " * (descConnLength - len(temp))
        self.exportConnsString = temp

        f = temp + "!" + str(self.trnsysId) + " : " + str(self.displayName) + "\n"

        return f, 1