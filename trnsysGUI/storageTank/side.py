import enum as _enum


class Side(_enum.Enum):
    LEFT = "left"
    RIGHT = "right"

    @staticmethod
    def createFromSideNr(sideNr: int) -> "Side":
        if sideNr == 2:
            return Side.RIGHT

        if sideNr == 0:
            return Side.LEFT

        raise ValueError(f"Unknown side number: {sideNr}")

    def toSideNr(self):
        if self == self.LEFT:
            return 0

        if self == self.RIGHT:
            return 2

        raise ValueError(f"Cannot convert {self} to side nr.")

    def formatDdck(self):
        if self == self.LEFT:
            return "Left"

        if self == self.RIGHT:
            return "Right"

        raise ValueError(f"Cannot convert {self} to side nr.")

    @property
    def isLeft(self) -> bool:
        return self == self.LEFT
