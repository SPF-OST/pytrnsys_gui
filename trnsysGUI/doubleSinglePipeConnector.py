import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.dPConnector import DPConnector
from trnsysGUI.DoublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.SinglePipePortItem import SinglePipePortItem  # type: ignore[attr-defined]


class DoubleSinglePipeConnector(DPConnector):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.typeNumber = 2

        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.DOUBLE_SINGLE_PIPE_CONNECTOR_SVG

    def changeSize(self):
        super().changeSize()
        self.origInputsPos = [[0, 0], [0, 20]]
        self.origOutputsPos = [[20, 10]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
