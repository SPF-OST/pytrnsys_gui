# pylint: skip-file

import typing as _tp

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


class HeatPumpTwoHx(
    _bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin
):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", self))

        self.outputs.append(_cspi.createSinglePipePortItem("o", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))

        # For restoring correct order of trnsysObj list
        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.editor.idGen.getTrnsysID())
        self.childIds.append(self.editor.idGen.getTrnsysID())

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    @classmethod
    @_tp.override
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.HP_TWO_HX_SVG

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

        self.origInputsPos = [
            [0, delta],
            [w, h - delta],
            [w, 2 * delta],
        ]  # inlet of [evap, cond, cond]
        self.origOutputsPos = [
            [0, h - delta],
            [w, h - 2 * delta],
            [w, delta],
        ]  # outlet of [evap, cond, cond]

        self.inputs[0].setPos(
            self.origInputsPos[0][0], self.origInputsPos[0][1]
        )  # evaporator
        self.inputs[1].setPos(
            self.origInputsPos[1][0], self.origInputsPos[1][1]
        )  # bottom condenser
        self.inputs[2].setPos(
            self.origInputsPos[2][0], self.origInputsPos[2][1]
        )  # top condenser
        self.outputs[0].setPos(
            self.origOutputsPos[0][0], self.origOutputsPos[0][1]
        )  # evaporator
        self.outputs[1].setPos(
            self.origOutputsPos[1][0], self.origOutputsPos[1][1]
        )  # bottom condenser
        self.outputs[2].setPos(
            self.origOutputsPos[2][0], self.origOutputsPos[2][1]
        )  # top condenser

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
            dct["HeatPumpPosition"] = (
                float(self.pos().x()),
                float(self.pos().y()),
            )
            dct["trnsysID"] = self.trnsysId
            dct["childIds"] = self.childIds
            dct["FlippedH"] = self.flippedH
            dct["FlippedV"] = self.flippedV
            dct["RotationN"] = self.rotationN

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resBlockList):
        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            self.logger.debug("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            self.logger.debug("Output at heatExchanger")

        self.setPos(
            float(i["HeatPumpPosition"][0]), float(i["HeatPumpPosition"][1])
        )
        self.trnsysId = i["trnsysID"]

        resBlockList.append(self)

    def getInternalPiping(self) -> _ip.InternalPiping:
        evaporatorInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        evaporatorOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        evaporatorPipe = _mfn.Pipe(evaporatorInput, evaporatorOutput, "Evap")

        condenser1Input = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        condenser1Output = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        condenser1Pipe = _mfn.Pipe(condenser1Input, condenser1Output, "Cond1")

        condenser2Input = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        condenser2Output = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        condenser2Pipe = _mfn.Pipe(condenser2Input, condenser2Output, "Cond2")

        modelPortItemsToGraphicalPortItem = {
            evaporatorInput: self.inputs[0],
            evaporatorOutput: self.outputs[0],
            condenser1Input: self.inputs[1],
            condenser1Output: self.outputs[1],
            condenser2Input: self.inputs[2],
            condenser2Output: self.outputs[2],
        }
        nodes = [evaporatorPipe, condenser1Pipe, condenser2Pipe]

        return _ip.InternalPiping(nodes, modelPortItemsToGraphicalPortItem)
