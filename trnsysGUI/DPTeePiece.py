import typing as _tp

import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.BlockItem import BlockItem # type: ignore[attr-defined]
from trnsysGUI.DoublePipePortItem import DoublePipePortItem # type: ignore[attr-defined]


class DPTeePiece(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(DPTeePiece, self).__init__(trnsysType, parent, **kwargs)

        self.w = 60
        self.h = 40

        self.typeNumber = 2

        self.inputs.append(DoublePipePortItem("i", 0, self))
        self.inputs.append(DoublePipePortItem("i", 2, self))
        self.outputs.append(DoublePipePortItem("o", 1, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        if self.rotationN % 4 == 0:
            return _img.DP_TEE_PIECE_SVG
        elif self.rotationN % 4 == 1:
            return _img.DP_TEE_PIECE_ROTATED_90
        elif self.rotationN % 4 == 2:
            return _img.DP_TEE_PIECE_ROTATED_180
        elif self.rotationN % 4 == 3:
            return _img.DP_TEE_PIECE_ROTATED_270

    def changeSize(self):
        self.origInputsPos = [[0, 30], [40, 30]]
        self.origOutputsPos = [[30, 0]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 1 - 1 * self.flippedH) % 4

    def getInternalPiping(self) -> InternalPiping:
        pass

    def _getModelAndMapping(self):
        pass

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        pass
