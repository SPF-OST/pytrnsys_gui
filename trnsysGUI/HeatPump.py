# pylint: skip-file

import os
import shutil
import typing as _tp

from PyQt5.QtWidgets import QTreeView

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip


class HeatPump(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", self))

        self.outputs.append(_cspi.createSinglePipePortItem("o", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))

        # For restoring correct order of trnsysObj list
        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.editor.idGen.getTrnsysID())

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.HP_SVG

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

        # upper left is reference
        self.origInputsPos = [[0, delta], [w, h - delta]]  # inlet of [evap, cond]
        self.origOutputsPos = [[0, h - delta], [w, delta]]  # outlet of [evap, cond]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])  # evaporator
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])  # condenser

        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        return w, h

    def encode(self):
        if self.isVisible():
            self.logger.debug("Encoding a HeatPump")

            portListInputs = []
            portListOutputs = []

            for p in self.inputs:
                portListInputs.append(p.id)
            for p in self.outputs:
                portListOutputs.append(p.id)

            dct = {}
            dct[".__BlockDict__"] = True
            dct["BlockName"] = self.name
            dct["BlockDisplayName"] = self.displayName
            dct["PortsIDIn"] = portListInputs
            dct["PortsIDOut"] = portListOutputs
            dct["HeatPumpPosition"] = (float(self.pos().x()), float(self.pos().y()))
            dct["trnsysID"] = self.trnsysId
            dct["childIds"] = self.childIds
            dct["FlippedH"] = self.flippedH
            dct["FlippedV"] = self.flippedV
            dct["RotationN"] = self.rotationN

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resBlockList):
        self.logger.debug("Loading a HeatPump block")

        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.rotationN = i["RotationN"]
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            self.logger.debug("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            self.logger.debug("Output at heatExchanger")

        self.setPos(float(i["HeatPumpPosition"][0]), float(i["HeatPumpPosition"][1]))
        self.trnsysId = i["trnsysID"]

        resBlockList.append(self)

    def getInternalPiping(self) -> _ip.InternalPiping:
        condenserInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        condenserOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        condenserPipe = _mfn.Pipe(condenserInput, condenserOutput, "Cond")

        evaporatorInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        evaporatorOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        evaporatorPipe = _mfn.Pipe(evaporatorInput, evaporatorOutput, "Evap")

        modelPortItemsToGraphicalPortItem = {
            condenserInput: self.inputs[1],
            condenserOutput: self.outputs[1],
            evaporatorInput: self.inputs[0],
            evaporatorOutput: self.outputs[0],
        }
        nodes = [condenserPipe, evaporatorPipe]

        return _ip.InternalPiping(nodes, modelPortItemsToGraphicalPortItem)
