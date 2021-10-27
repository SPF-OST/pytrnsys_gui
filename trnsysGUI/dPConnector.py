
import typing as _tp

import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]


class DPConnector(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 20
        self.h = 20

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        raise NotImplementedError()

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

    def getInternalPiping(self) -> InternalPiping:
        pass

    def _getModelAndMapping(self):
        pass

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        pass
