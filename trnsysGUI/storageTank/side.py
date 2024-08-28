import enum as _enum

import trnsysGUI.sideNrs as _snrs


class Side(_enum.Enum):
    LEFT = "left"
    RIGHT = "right"

    @staticmethod
    def createFromSideNr(sideNr: int) -> "Side":
        if sideNr == _snrs.SideNrs.RIGHT:
            return Side.RIGHT

        if sideNr == _snrs.SideNrs.LEFT:
            return Side.LEFT

        raise ValueError(f"Unknown side number: {sideNr}")

    def toSideNr(self) -> _snrs.SideNr:
        if self == self.LEFT:
            return _snrs.SideNrs.LEFT

        if self == self.RIGHT:
            return _snrs.SideNrs.RIGHT

        raise ValueError(f"Cannot convert {self} to side nr.")

    def formatDdck(self) -> str:
        if self == self.LEFT:
            return "Left"

        if self == self.RIGHT:
            return "Right"

        raise ValueError(f"Cannot convert {self} to side nr.")

    @property
    def isLeft(self) -> bool:
        return self == self.LEFT
