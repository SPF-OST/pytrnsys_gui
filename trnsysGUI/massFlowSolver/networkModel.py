__all__ = [
    "NodeType",
    "PortItem",
    "OneNeighbourBase",
    "Source",
    "Sink",
    "TwoNeighboursBase",
    "Pipe",
    "Pump",
    "ThreeNeighboursBase",
    "TeePiece",
    "Diverter",
]

import abc as _abc
import dataclasses as _dc
import enum as _enum
import typing as _tp


class NodeType(_enum.IntEnum):
    PIPE = 0
    PUMP = 1
    TEE_PIECE = 2
    DIVERTER = 3
    SOURCE = 4
    SINK = 5


@_dc.dataclass(eq=False)
class InputVariable:
    UNDEFINED_INPUT_VARIABLE_VALUE = "0,0"
    name: str


@_dc.dataclass(eq=False)
class OutputVariable:
    name: str


OutputVariableIndex = _tp.Literal[1, 2, 3]

MAX_N_OUTPUT_VARIABLES_PER_NODE = 3

OutputVariables = _tp.Tuple[_tp.Optional[OutputVariable], _tp.Optional[OutputVariable], _tp.Optional[OutputVariable]]


class PortItemDirection(_enum.Enum):
    INPUT = "Input"
    OUTPUT = "Output"


class PortItemType(_enum.Enum):
    STANDARD = "standard"
    HOT = "hot"
    COLD = "cold"

    def isCompatibleWith(self, otherType) -> bool:
        return self in (self.STANDARD, otherType)


@_dc.dataclass(eq=False, repr=False)
class PortItem:
    name: str
    direction: PortItemDirection
    type: PortItemType = PortItemType.STANDARD

    def canOverlapWith(self, other: "PortItem") -> bool:
        """Can this model port item overlap with `other` under a graphical port item?"""
        return self.type.isCompatibleWith(other.type)


class Node(_abc.ABC):
    def __init__(self, name: _tp.Optional[str]) -> None:
        self.name = name

    @_abc.abstractmethod
    def getPortItems(self) -> _tp.Sequence["PortItem"]:
        raise NotImplementedError()

    @_abc.abstractmethod
    def getNodeType(self) -> NodeType:
        raise NotImplementedError()

    def hasInput(self) -> bool:
        return False

    def getInputVariablePrefix(self) -> str:
        raise ValueError(f"`{type(self).__name__}` doesn't have an input variable prefix.")


class OneNeighbourBase(Node, _abc.ABC):
    def __init__(self, portItem: PortItem, name: _tp.Optional[str] = None) -> None:
        super().__init__(name)
        self.portItem = portItem

    def getPortItems(self) -> _tp.Sequence[PortItem]:
        return [self.portItem]


class Source(OneNeighbourBase):
    def getNodeType(self) -> NodeType:
        return NodeType.SOURCE

    def hasInput(self) -> bool:
        return True

    def getInputVariablePrefix(self) -> str:
        return "Mfr"


class Sink(OneNeighbourBase):
    def getNodeType(self) -> NodeType:
        return NodeType.SINK


class TwoNeighboursBase(Node, _abc.ABC):
    def __init__(self, fromPort: PortItem, toPort: PortItem, name: _tp.Optional[str] = None) -> None:
        super().__init__(name)
        self.fromPort = fromPort
        self.toPort = toPort

    def getPortItems(self) -> _tp.Sequence[PortItem]:
        return [self.fromPort, self.toPort]


class Pipe(TwoNeighboursBase):
    def getNodeType(self) -> NodeType:
        return NodeType.PIPE


class Pump(TwoNeighboursBase):
    def getNodeType(self) -> NodeType:
        return NodeType.PUMP

    def hasInput(self) -> bool:
        return True

    def getInputVariablePrefix(self) -> str:
        return "Mfr"


class ThreeNeighboursBase(Node, _abc.ABC):
    def __init__(
        self, inputPort: PortItem, output1Port: PortItem, output2Port: PortItem, name: _tp.Optional[str] = None
) -> None:
        super().__init__(name)
        self.input = inputPort
        self.output1 = output1Port
        self.output2 = output2Port

    def getPortItems(self) -> _tp.Sequence[PortItem]:
        return [self.input, self.output1, self.output2]


class Diverter(ThreeNeighboursBase):
    def getNodeType(self) -> NodeType:
        return NodeType.DIVERTER

    def hasInput(self) -> bool:
        return True

    def getInputVariablePrefix(self) -> str:
        return "xFrac"


class TeePiece(ThreeNeighboursBase):
    def getNodeType(self) -> NodeType:
        return NodeType.TEE_PIECE
