__all__ = [
    "NodeType",
    "NodeBase",
    "PortItem",
    "RealNodeBase",
    "OneNeighbourBase",
    "Source",
    "Sink",
    "TwoNeighboursBase",
    "Pipe",
    "Pump",
    "ThreeNeighboursBase",
    "TeePiece",
    "Diverter",
    "getConnectedNodes",
    "getConnectedRealNodesAndPortItems",
]

import abc as _abc
import dataclasses as _dc
import enum as _enum
import typing as _tp
import collections.abc as _cabc


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


class NodeBase(_abc.ABC):
    @_abc.abstractmethod
    def getNeighbours(self) -> _tp.Sequence["NodeBase"]:
        raise NotImplementedError()


class PortItemType(_enum.Enum):
    INPUT = "Input"
    OUTPUT = "Output"


@_dc.dataclass(eq=False, repr=False)
class PortItem(NodeBase, _abc.ABC):
    name: str
    type: PortItemType

    def getNeighbours(self) -> _tp.Sequence[NodeBase]:
        return []

    def canOverlapWith(self, other: "PortItem") -> bool:
        """Can this model port item overlap with `other` under a graphical port item?"""
        return other != self


@_dc.dataclass(eq=False)  # type: ignore[misc]
class RealNodeBase(NodeBase, _abc.ABC):
    name: str
    trnsysId: int

    @_abc.abstractmethod
    def getNodeType(self) -> NodeType:
        raise NotImplementedError()

    def getInputVariable(self) -> _tp.Optional[InputVariable]:  # pylint: disable=no-self-use
        return None

    def getOutputVariables(self) -> OutputVariables:
        return (
            self._getOutputVariable(1, "A"),
            self._getOutputVariable(2, "B"),
            self._getOutputVariable(3, "C"),
        )

    def _getOutputVariable(self, variableIndex: OutputVariableIndex, postfix: str) -> _tp.Optional[OutputVariable]:
        if variableIndex > self._getNumberOfOutputVariables():
            return None

        return OutputVariable(f"Mfr{self.name}_{postfix}")

    @_abc.abstractmethod
    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        raise NotImplementedError()


@_dc.dataclass(eq=False)  # type: ignore[misc]
class OneNeighbourBase(RealNodeBase, _abc.ABC):
    neighbour: NodeBase

    def getNeighbours(self) -> _tp.Sequence[NodeBase]:
        return [self.neighbour]


class Source(OneNeighbourBase):
    def getNodeType(self) -> NodeType:
        return NodeType.SOURCE

    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        return 2

    def getInputVariable(self) -> _tp.Optional[InputVariable]:
        return InputVariable(f"Mfr{self.name}")


class Sink(OneNeighbourBase):
    def getNodeType(self) -> NodeType:
        return NodeType.SINK

    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        return 2


@_dc.dataclass(eq=False)  # type: ignore[misc]
class TwoNeighboursBase(RealNodeBase, _abc.ABC):
    fromNode: NodeBase
    toNode: NodeBase

    def getNeighbours(self) -> _tp.Sequence[NodeBase]:
        return [self.fromNode, self.toNode]

    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        return 2


class Pipe(TwoNeighboursBase):
    def getNodeType(self) -> NodeType:
        return NodeType.PIPE

    @property
    def fromPort(self) -> PortItem:
        assert isinstance(self.fromNode, PortItem)
        return self.fromNode

    @property
    def toPort(self) -> PortItem:
        assert isinstance(self.toNode, PortItem)
        return self.toNode


class Pump(TwoNeighboursBase):
    def getNodeType(self) -> NodeType:
        return NodeType.PUMP

    def getInputVariable(self) -> _tp.Optional[InputVariable]:
        return InputVariable(f"Mfr{self.name}")


@_dc.dataclass(eq=False)  # type: ignore[misc]
class ThreeNeighboursBase(RealNodeBase, _abc.ABC):
    node1: NodeBase
    node2: NodeBase
    node3: NodeBase

    def getNeighbours(self) -> _tp.Sequence[NodeBase]:
        return [self.node1, self.node2, self.node3]

    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        return 3


class Diverter(ThreeNeighboursBase):
    def getNodeType(self) -> NodeType:
        return NodeType.DIVERTER

    def getInputVariable(self) -> _tp.Optional[InputVariable]:
        return InputVariable(f"xFrac{self.name}")


class TeePiece(ThreeNeighboursBase):
    def getNodeType(self) -> NodeType:
        return NodeType.TEE_PIECE


def getConnectedNodes(startingNode: NodeBase) -> _tp.Sequence[NodeBase]:
    nodes = {startingNode}
    neighbours = _getNeighboursForNodes(nodes)
    while neighbours:
        nodes |= neighbours
        neighbours = _getNeighboursForNodes(nodes)

    return list(nodes)


def _getNeighboursForNodes(nodes: _cabc.Set[NodeBase]) -> _cabc.Set[NodeBase]:
    neighbours = {neighbour for node in nodes for neighbour in node.getNeighbours() if neighbour not in nodes}
    return neighbours


@_dc.dataclass
class RealNodesAndPortItems:
    realNodes: _tp.Sequence[RealNodeBase]
    portItems: _tp.Sequence[PortItem]


def getConnectedRealNodesAndPortItems(startingNode: NodeBase) -> RealNodesAndPortItems:
    connectedNodes = getConnectedNodes(startingNode)
    realNodes = [n for n in connectedNodes if isinstance(n, RealNodeBase)]
    portItems = [n for n in connectedNodes if isinstance(n, PortItem)]
    return RealNodesAndPortItems(realNodes, portItems)
