# pylint: skip-file
# type: ignore

import typing as _tp

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.massFlowSolver import InternalPiping, MassFlowNetworkContributorMixin


class TeePiece(BlockItem, MassFlowNetworkContributorMixin):
    def __init__(self, trnsysType, parent, **kwargs):
        super(TeePiece, self).__init__(trnsysType, parent, **kwargs)

        self.w = 40
        self.h = 40

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 1, self))

        self.changeSize()

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

        self.origInputsPos = [[0, delta]]
        self.origOutputsPos = [[w, delta], [delta, 0]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 1 - 2 * self.flippedV) % 4

        return w, h

    def getInternalPiping(self) -> InternalPiping:
        teePiece, modelPortItemsToGraphicalPortItem = self._getModelAndMapping()

        internalPiping = InternalPiping([teePiece], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def _getModelAndMapping(self):
        input = _mfn.PortItem("input", _mfn.PortItemType.INPUT)
        output1 = _mfn.PortItem("straightOutput", _mfn.PortItemType.OUTPUT)
        output2 = _mfn.PortItem("orthogonalOutput", _mfn.PortItemType.OUTPUT)
        teePiece = _mfn.TeePiece(self.displayName, self.trnsysId, input, output1, output2)
        modelPortItemsToGraphicalPortItem = {input: self.inputs[0], output1: self.outputs[0], output2: self.outputs[1]}
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

            assert len(openLoop.realNodes) == 1
            realNode = openLoop.realNodes[0]

            outputVariables = realNode.serialize(nodesToIndices).outputVariables
            for outputVariable in outputVariables:
                if not outputVariable:
                    continue

                unitText += outputVariable.name + "\n"

            unitText += f"T{self.inputs[0].connectionList[0].displayName}\n"
            unitText += f"T{self.inputs[1].connectionList[0].displayName}\n"
            unitText += f"T{self.outputs[0].connectionList[0].displayName}\n"

            unitText += "***Initial values\n"
            unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

            unitText += "EQUATIONS 1\n"
            unitText += "T" + self.displayName + "= [" + str(unitNumber) + "," + str(equationConstant) + "]\n"

            unitNumber += 1
            f += unitText + "\n"

            return f, unitNumber
        else:
            return "", startingUnit
