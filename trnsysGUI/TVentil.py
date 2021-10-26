# pylint: skip-file
# type: ignore

import typing as _tp

from PyQt5.QtWidgets import QGraphicsTextItem

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.SinglePipePortItem import SinglePipePortItem


class TVentil(BlockItem, _mfs.MassFlowNetworkContributorMixin):
    def __init__(self, trnsysType, parent, **kwargs):
        super(TVentil, self).__init__(trnsysType, parent, **kwargs)

        self.h = 40
        self.w = 40
        self.typeNumber = 3
        self.isTempering = False
        self.positionForMassFlowSolver = 1.0
        self.posLabel = QGraphicsTextItem(str(self.positionForMassFlowSolver), self)
        self.posLabel.setVisible(False)


        self.inputs.append(SinglePipePortItem("o", 0, self))
        self.inputs.append(SinglePipePortItem("o", 1, self))
        self.outputs.append(SinglePipePortItem("i", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.T_VENTIL_SVG

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

        self.label.setPos(lx, h - self.flippedV * (h + h / 2))
        self.posLabel.setPos(lx + 5, -15)

        self.origInputsPos = [[0, delta], [delta, 0]]
        self.origOutputsPos = [[w, delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 1 + 2 * self.flippedV) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

    def rotateBlockCW(self):
        super().rotateBlockCW()
        # Rotate valve position label back so it will always stay horizontal
        self._updateRotation()

    def rotateBlockCCW(self):
        super().rotateBlockCCW()
        # Rotate valve position label back so it will always stay horizontal
        self._updateRotation()

    def resetRotation(self):
        super().resetRotation()
        # Rotate valve position label back so it will always stay horizontal
        self._updateRotation()

    def _updateRotation(self):
        self.posLabel.setRotation(-self.rotationN * 90)

    def setComplexDiv(self, b):
        self.isTempering = bool(b)

    def setPositionForMassFlowSolver(self, f):
        self.positionForMassFlowSolver = f

    def encode(self):
        dictName, dct = super(TVentil, self).encode()
        dct["IsTempering"] = self.isTempering
        dct["PositionForMassFlowSolver"] = self.positionForMassFlowSolver
        return dictName, dct

    def decode(self, i, resBlockList):
        super().decode(i, resBlockList)
        if "IsTempering" not in i or "PositionForMassFlowSolver" not in i:
            self.logger.debug("Old version of diagram")
            self.positionForMassFlowSolver = 1.0
        else:
            self.isTempering = i["IsTempering"]
            self.positionForMassFlowSolver = i["PositionForMassFlowSolver"]

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        super(TVentil, self).decodePaste(i, offset_x, offset_y, resConnList, resBlockList, **kwargs)
        if "IsTempering" or "PositionForMassFlowSolver" not in i:
            self.logger.debug("Old version of diagram")
            self.positionForMassFlowSolver = 1.0
        else:
            self.isTempering = i["IsTempering"]
            self.positionForMassFlowSolver = i["PositionForMassFlowSolver"]

    def exportMassFlows(self):
        if not self.isTempering:
            resStr = "xFrac" + self.displayName + " = " + str(self.positionForMassFlowSolver) + "\n"
            equationNr = 1
            return resStr, equationNr
        else:
            return "", 0

    def exportDivSetting1(self):
        if self.isTempering:
            constants = 1
            f = "T_set_" + self.displayName + "=50\n"
            return f, constants
        else:
            return "", 0

    def exportDivSetting2(self, nUnit):
        if self.isTempering:
            f = ""
            nUnit = nUnit + 1
            f += "UNIT %d TYPE 811 ! Passive Divider for heating \n" % nUnit
            f += "PARAMETERS 1" + "\n"
            f += "5 !Nb.of iterations before fixing the value \n"
            f += "INPUTS 4 \n"

            if (
                self.outputs[0].pos().y() == self.inputs[0].pos().y()
                or self.outputs[0].pos().x() == self.inputs[0].pos().x()
            ):
                first = self.inputs[0]
                second = self.inputs[1]

            f += "T" + first.connectionList[0].displayName + "\n"
            f += "T" + second.connectionList[0].displayName + "\n"
            f += "Mfr" + self.outputs[0].connectionList[0].displayName + "\n"

            f += "T_set_" + self.displayName + "\n"
            f += "*** INITIAL INPUT VALUES" + "\n"
            f += "35.0 21.0 800.0 T_set_" + self.displayName + "\n"

            f += "EQUATIONS 1\n"
            f += "xFrac" + self.displayName + " =  1.-[%d,5] \n\n" % nUnit

            return f, nUnit
        else:
            return "", nUnit

    def getInternalPiping(self) -> _mfs.InternalPiping:
        teePiece, modelPortItemsToGraphicalPortItem = self._getModelAndMapping()

        return _mfs.InternalPiping([teePiece], modelPortItemsToGraphicalPortItem)

    def _getModelAndMapping(self):
        input1 = _mfn.PortItem()
        input2 = _mfn.PortItem()
        output = _mfn.PortItem()
        teePiece = _mfn.Diverter(self.displayName, self.trnsysId, output, input1, input2)
        modelPortItemsToGraphicalPortItem = {input1: self.inputs[0], input2: self.inputs[1], output: self.outputs[0]}
        return teePiece, modelPortItemsToGraphicalPortItem

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

            openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
            assert len(openLoops) == 1
            openLoop = openLoops[0]

            realNodes = [n for n in openLoop.nodes if isinstance(n, _mfn.RealNodeBase)]
            assert len(realNodes) == 1
            realNode = realNodes[0]

            outputVariables = realNode.serialize(nodesToIndices).outputVariables
            for outputVariable in outputVariables:
                if not outputVariable:
                    continue

                unitText += outputVariable.name + "\n"

            unitText += f"T{self.outputs[0].connectionList[0].displayName}\n"
            unitText += f"T{self.inputs[0].connectionList[0].displayName}\n"
            unitText += f"T{self.inputs[1].connectionList[0].displayName}\n"

            unitText += "***Initial values\n"
            unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

            unitText += "EQUATIONS 1\n"
            unitText += "T" + self.displayName + "= [" + str(unitNumber) + "," + str(equationConstant) + "]\n"

            unitNumber += 1
            f += unitText + "\n"

            return f, unitNumber
        else:
            return "", startingUnit
