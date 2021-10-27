
import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.BlockItem import BlockItem # type: ignore[attr-defined]
from trnsysGUI.DoublePipePortItem import DoublePipePortItem # type: ignore[attr-defined]


class DoubleDoublePipeConnector(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 20
        self.h = 20

        self.typeNumber = 2

        self.inputs.append(DoublePipePortItem("i", 0, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.DOUBLE_DOUBLE_PIPE_CONNECTOR_SVG

    def rotateBlockCW(self):
        super().rotateBlockCW()
        self._flipPipes()

    def rotateBlockCCW(self):
        super().rotateBlockCCW()
        self._flipPipes()

    def _flipPipes(self):
        angle = (self.rotationN % 4) * 90
        if angle == 0:
            self.updateFlipStateV(False)
        elif angle == 90:
            self.updateFlipStateV(True)
        elif angle == 180:
            self.updateFlipStateV(True)
        elif angle == 270:
            self.updateFlipStateV(False)

    def resetRotation(self):
        super().resetRotation()
        self.updateFlipStateV(0)

    def changeSize(self):
        w = self.w
        h = self.h

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 20:
            w = 20

        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2

        self.label.setPos(lx, h - self.flippedV * (h + h / 2))

        self.origInputsPos = [[0, 10]]
        self.origOutputsPos = [[20, 10]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

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
