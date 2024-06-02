import typing as _tp

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip


class Crystalizer(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.w = 120
        self.h = 40

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    def _getImageAccessor(self) -> _img.SvgImageAccessor:
        return _img.CRYSTALIZER_SVG

    def changeSize(self):
        self._positionLabel()

        self.origInputsPos = [[0, 20]]
        self.origOutputsPos = [[120, 20]]

        # pylint: disable=duplicate-code  # 2
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 0 + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 + 2 * self.flippedH) % 4
        # pylint: disable=duplicate-code  # 2

    def getInternalPiping(self) -> _ip.InternalPiping:
        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)

        crystalizer = _mfn.Pipe(inputPort, outputPort)
        modelPortItemsToGraphicalPortItem = {inputPort: self.inputs[0], outputPort: self.outputs[0]}
        return _ip.InternalPiping([crystalizer], modelPortItemsToGraphicalPortItem)
