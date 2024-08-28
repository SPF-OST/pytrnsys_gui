# pylint: skip-file

import typing as _tp

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


class Boiler(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)
        self.w = 80
        self.h = 120
        self.portOffset = 5
        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.BOILER_SVG

    def changeSize(self):
        self.logger.debug("passing through c change size")
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 20
        deltaH = self.h / 10

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

        self.origInputsPos = [[w, h - delta]]
        self.origOutputsPos = [[w, delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        return w, h

    def getInternalPiping(self) -> _ip.InternalPiping:
        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        pipe = _mfn.Pipe(inputPort, outputPort)

        return _ip.InternalPiping([pipe], {inputPort: self.inputs[0], outputPort: self.outputs[0]})
