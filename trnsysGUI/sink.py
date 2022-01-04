import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.sourceSinkBase import SourceSinkBase


class Sink(SourceSinkBase):
    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SINK_SVG

    def changeSize(self):
        self._positionLabel()

        self.origInputsPos = [[40, 0]]
        self.origOutputsPos = [[20, 0]]

        # pylint: disable=duplicate-code  # 1
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 1 + 2 * self.flippedV) % 4
        self.outputs[0].side = (self.rotationN + 1 + 2 * self.flippedV) % 4
        # pylint: disable=duplicate-code  # 1
