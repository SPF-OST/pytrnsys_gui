import dataclasses as _dc

import trnsysGUI.PortItem as _port


@_dc.dataclass
class DirectPortPair:
    name: str
    fromPort: _port.PortItem  # type: ignore[name-defined]
    toPort: _port.PortItem  # type: ignore[name-defined]
    relativeInputHeight: float
    relativeOutputHeight: float
    isOnLeftSide: bool

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

    @property
    def side(self) -> str:
        return "Left" if self.isOnLeftSide else "Right"
