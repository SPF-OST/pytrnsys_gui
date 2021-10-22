# pylint: skip-file
# type: ignore

import typing as _tp

import numpy as np

import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.SinglePipePortItem import SinglePipePortItem


class Pump(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(Pump, self).__init__(trnsysType, parent, **kwargs)
        self.w = 40
        self.h = 40
        self.typeNumber = 1
        self.rndPwr = np.random.randint(0, 1000)

        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.outputs.append(SinglePipePortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.PUMP_SVG

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

        self.origInputsPos = [[0, delta]]
        self.origOutputsPos = [[w, delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

    def exportBlackBox(self):
        return "noBlackBoxOutput", []

    def exportPumpOutlets(self):
        f = "T" + self.displayName + " = " + "T" + self.inputs[0].connectionList[0].displayName + "\n"
        equationNr = 1
        return f, equationNr

    def exportMassFlows(self):
        equationNr = 1
        massFlowLine = f"Mfr{self.displayName} = {self.rndPwr}\n"
        return massFlowLine, equationNr

    def getInternalPiping(self) -> InternalPiping:
        inputPort = _mfn.PortItem()
        outputPort = _mfn.PortItem()

        pump = _mfn.Pump(self.displayName, self.trnsysId, inputPort, outputPort)

        modelPortItemsToGraphicalPortItem = {inputPort: self.inputs[0], outputPort: self.outputs[0]}
        return InternalPiping([pump], modelPortItemsToGraphicalPortItem)
