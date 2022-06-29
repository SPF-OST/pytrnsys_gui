import dataclasses as _dc

import trnsysGUI.singlePipePortItem as _port
import trnsysGUI.storageTank.side as _sd

import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class DirectPortPair:
    trnsysId: int
    fromPort: _port.SinglePipePortItem  # type: ignore[name-defined]
    toPort: _port.SinglePipePortItem  # type: ignore[name-defined]
    relativeInputHeight: float
    relativeOutputHeight: float
    side: _sd.Side
    modelPipe: _mfn.Pipe = _dc.field(init=False)

    def __post_init__(self):
        self._updateModelPipe()

    @property
    def relativeInputHeightPercent(self):
        return self._toPercent(self.relativeInputHeight)

    @property
    def relativeOutputHeightPercent(self):
        return self._toPercent(self.relativeOutputHeight)

    def setRelativeHeights(
        self, relativeInputHeight: float, relativeOutputHeight: float, storageTankHeight: float
    ) -> None:
        self.relativeInputHeight = relativeInputHeight
        self.relativeOutputHeight = relativeOutputHeight

        inputPosY = storageTankHeight - storageTankHeight * self.relativeInputHeight
        self.fromPort.setY(inputPosY)

        outputPosY = storageTankHeight - storageTankHeight * self.relativeOutputHeight
        self.toPort.setY(outputPosY)

        self._updateModelPipe()

    def _updateModelPipe(self) -> None:
        self.modelPipe = self._createModelPipe()

    def _createModelPipe(self) -> _mfn.Pipe:
        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        name = self._getModelPipeName()
        modelPipe = _mfn.Pipe(inputPort, outputPort, name)
        return modelPipe

    def _getModelPipeName(self) -> str:
        name = (
            f"Dp{'L' if self.side.isLeft else 'R'}{self.relativeInputHeightPercent}_{self.relativeOutputHeightPercent}"
        )
        return name

    @staticmethod
    def _toPercent(relativeHeight: float):
        return int(round(relativeHeight * 100, 2))
