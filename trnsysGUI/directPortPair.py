import dataclasses as _dc

import trnsysGUI.Connection as _conn
import trnsysGUI.PortItem as _port


@_dc.dataclass
class DirectPortPair:
    connection: _conn.Connection  # type: ignore[name-defined]
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
    def name(self) -> str:
        return self.connection.displayName

    @property
    def fromPort(self) -> _port.PortItem:  # type: ignore[name-defined]
        return self.connection.fromPort

    @property
    def toPort(self) -> _port.PortItem:  # type: ignore[name-defined]
        return self.connection.toPort

    @property
    def side(self) -> str:
        return self.connection.side
