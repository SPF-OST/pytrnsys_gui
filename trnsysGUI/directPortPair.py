import dataclasses as _dc

from trnsysGUI.Connection import Connection  # type: ignore[attr-defined]


@_dc.dataclass
class DirectPortPair:
    connection: Connection
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
        self.connection.fromPort.setY(inputPosY)

        outputPosY = storageTankHeight - storageTankHeight*self.relativeOutputHeight
        self.connection.toPort.setY(outputPosY)
