import dataclasses as _dc

from trnsysGUI.Connection import Connection


@_dc.dataclass
class DirectPortPair:
    connection: Connection
    relativeInputHeight: float
    relativeOutputHeight: float
    isOnLeftSide: bool
