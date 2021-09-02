import dataclasses as _dc

import trnsysGUI.PortItem as _port
import trnsysGUI.storageTank.side as _sd


@_dc.dataclass
class DirectPortPair:
    trnsysId: int
    fromPort: _port.PortItem  # type: ignore[name-defined]
    toPort: _port.PortItem  # type: ignore[name-defined]
    relativeInputHeight: float
    relativeOutputHeight: float
    side: _sd.Side

    @property
    def relativeInputHeightPercent(self):
        return self._toPercent(self.relativeInputHeight)

    @property
    def relativeOutputHeightPercent(self):
        return self._toPercent(self.relativeOutputHeight)

    def setRelativeHeights(self,
                           relativeInputHeight: float,
                           relativeOutputHeight: float,
                           storageTankHeight: float) -> None:
        self.relativeInputHeight = relativeInputHeight
        self.relativeOutputHeight = relativeOutputHeight

        inputPosY = storageTankHeight - storageTankHeight*self.relativeInputHeight
        self.fromPort.setY(inputPosY)

        outputPosY = storageTankHeight - storageTankHeight*self.relativeOutputHeight
        self.toPort.setY(outputPosY)

    @staticmethod
    def _toPercent(relativeHeight: float):
        return int(round(relativeHeight * 100, 2))
