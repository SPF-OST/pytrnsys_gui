# pylint: skip-file
# type: ignore

import typing as _tp

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem
import trnsysGUI.images as _img


class WTap_main(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(WTap_main, self).__init__(trnsysType, parent, **kwargs)
        self.w = 40
        self.h = 40
        # self.inputs.append(PortItem('i', 0, self))
        self.outputs.append(PortItem("o", 0, self))

        self.exportInitialInput = 0.0

        self.typeNumber = 4

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.W_TAP_MAIN_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 20

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

        self.origOutputsPos = [[0, delta]]
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4

        return w, h

    def exportBlackBox(self):
        equation = ["T" + self.displayName + "=Tcw"]
        return "success", equation

    def exportMassFlows(self):
        resStr = "Mfr" + self.displayName + " = 1000" + "\n"
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

    def exportInputsFlowSolver1(self):
        temp1 = "Mfr" + self.displayName
        self.exportInputName = " " + temp1 + " "
        return self.exportInputName, 1
