# pylint: skip-file

import typing as _tp

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


class ParabolicTroughField(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.w = 160
        self.h = 240
        self.inputs.append(_cspi.createSinglePipePortItem("i", 2, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    def getInternalPiping(self) -> _ip.InternalPiping:
        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        pipe = _mfn.Pipe(inputPort, outputPort)

        return _ip.InternalPiping([pipe], {inputPort: self.inputs[0], outputPort: self.outputs[0]})

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.PT_FIELD_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        delta = 20

        if h < 20:
            h = 20
        if w < 40:
            w = 40

        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.origInputsPos = [[4 * delta, h]]
        self.origOutputsPos = [[4 * delta, 0]]

        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h
