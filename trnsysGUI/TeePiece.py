# pylint: skip-file
# type: ignore

import typing as _tp

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.PortItem import PortItem
import trnsysGUI.images as _img


class TeePiece(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(TeePiece, self).__init__(trnsysType, parent, **kwargs)

        self.w = 40
        self.h = 40

        self.typeNumber = 2

        self.inputs.append(PortItem("i", 0, self))
        self.inputs.append(PortItem("i", 2, self))
        self.outputs.append(PortItem("o", 1, self))

        self.changeSize()

        # self.addTree()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.TEE_PIECE_SVG

    def changeSize(self):
        w = self.w
        h = self.h

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

        deltaH = self.h / 8

        self.label.setPos(lx, h - self.flippedV * (h + h / 2))

        self.origInputsPos = [[0, delta], [w, delta]]
        self.origOutputsPos = [[delta, 0]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 1 - 1 * self.flippedH) % 4

        return w, h

    def exportParametersFlowSolver(self, descConnLength):
        temp = ""
        for i in self.inputs:
            for c in i.connectionList:
                temp = temp + str(c.trnsysId) + " "
                self.trnsysConn.append(c)

        for o in self.outputs:
            for c in o.connectionList:
                temp = temp + str(c.trnsysId) + " "
                self.trnsysConn.append(c)

        temp += str(self.typeNumber)
        temp += " " * (descConnLength - len(temp))
        self.exportConnsString = temp

        f = temp + "!" + str(self.trnsysId) + " : " + str(self.displayName) + "\n"

        return f

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        if self.isVisible():
            tot = ""
            for i in range(0, 3):
                temp = (
                    prefix
                    + self.displayName
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
                equationNumber += 1  # DC-ERR
            return tot, equationNumber, 3
        else:
            return "", equationNumber + 3, 0

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        if self.isVisible():
            f = ""
            unitNumber = startingUnit
            tNr = 929  # Temperature calculation from a tee-piece

            unitText = ""
            ambientT = 20

            equationConstant = 1

            unitText += "UNIT " + str(unitNumber) + " TYPE " + str(tNr) + "\n"
            unitText += "!" + self.displayName + "\n"
            unitText += "PARAMETERS 0\n"
            unitText += "INPUTS 6\n"

            for s in self.exportEquations:
                unitText += s[0 : s.find("=")] + "\n"

            for it in self.trnsysConn:
                unitText += "T" + it.displayName + "\n"

            unitText += "***Initial values\n"
            unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

            unitText += "EQUATIONS 1\n"
            unitText += "T" + self.displayName + "= [" + str(unitNumber) + "," + str(equationConstant) + "]\n"

            unitNumber += 1
            f += unitText + "\n"

            return f, unitNumber
        else:
            return "", startingUnit
