__all__ = [
    "NodeType",
    "Parameters",
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
class Parameters:
    UNUSED_INDEX_VALUE = 0

    name: str
    index: int

    nodeType: NodeType

    neighbourIndices: _tp.Tuple[int, int, int]

    def toString(self, secondColumnIndent: int) -> str:
        firstColumn = f"{self.neighbourIndices[0]} {self.neighbourIndices[1]} {self.neighbourIndices[2]} {self.nodeType} "
        secondColumn = f"!{self.index} : {self.name}"

        line = f"{firstColumn.ljust(secondColumnIndent)}{secondColumn}"

        return line


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


@_dc.dataclass(eq=False)
class SerializedNode:
    parameters: Parameters
    inputVariable: _tp.Optional[InputVariable]
    outputVariables: OutputVariables


class NodeBase(_abc.ABC):
    @_abc.abstractmethod
    def getNeighbours(self) -> _tp.Sequence["NodeBase"]:
        raise NotImplementedError()


@_dc.dataclass(eq=False)
class PortItem(NodeBase, _abc.ABC):
    def getNeighbours(self) -> _tp.Sequence[NodeBase]:
        return []

    def __repr__(self):
        return f"<PortItem object at 0x{id(self):x}>"


@_dc.dataclass(eq=False)
class RealNodeBase(NodeBase, _abc.ABC):
    name: str
    trnsysId: int

    def serialize(self, nodesToIndices: _tp.Mapping[NodeBase, int]) -> SerializedNode:
        parameters = self._getParameters(nodesToIndices)
        inputVariable = self._getInputVariable()
        outputVariables = self._getOutputVariables()
        return SerializedNode(parameters, inputVariable, outputVariables)

    def _getParameters(self, nodesToIndices: _tp.Mapping[NodeBase, int]) -> Parameters:
        index = nodesToIndices[self]
        neighbourIndices = self._getNeighbourIndices(nodesToIndices)
        return Parameters(self.name, index, self._getNodeType(), neighbourIndices)

    @_abc.abstractmethod
    def _getNodeType(self) -> NodeType:
        raise NotImplementedError()

    @_abc.abstractmethod
    def _getNeighbourIndices(self, nodesToIndices: _tp.Mapping["NodeBase", int]) -> _tp.Tuple[int, int, int]:
        raise NotImplementedError()

    def _getInputVariable(self) -> _tp.Optional[InputVariable]:
        return None

    def _getOutputVariables(self) -> OutputVariables:
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


@_dc.dataclass(eq=False)
class OneNeighbourBase(RealNodeBase, _abc.ABC):
    neighbour: NodeBase

    def getNeighbours(self) -> _tp.Sequence[NodeBase]:
        return [self.neighbour]


class Source(OneNeighbourBase):
    def _getNodeType(self) -> NodeType:
        return NodeType.SOURCE

    def _getNeighbourIndices(self, nodesToIndices: _tp.Mapping["NodeBase", int]) -> _tp.Tuple[int, int, int]:
        neighbourIndex = nodesToIndices[self.neighbour]
        return neighbourIndex, Parameters.UNUSED_INDEX_VALUE, Parameters.UNUSED_INDEX_VALUE

    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        return 2

    def _getInputVariable(self) -> _tp.Optional[InputVariable]:
        return InputVariable(f"Mfr{self.name}")


class Sink(OneNeighbourBase):
    def _getNodeType(self) -> NodeType:
        return NodeType.SINK

    def _getNeighbourIndices(self, nodesToIndices: _tp.Mapping["NodeBase", int]) -> _tp.Tuple[int, int, int]:
        neighbourIndex = nodesToIndices[self.neighbour]
        return neighbourIndex, Parameters.UNUSED_INDEX_VALUE, Parameters.UNUSED_INDEX_VALUE

    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        return 2


@_dc.dataclass(eq=False)
class TwoNeighboursBase(RealNodeBase, _abc.ABC):
    fromNode: NodeBase
    toNode: NodeBase

    def getNeighbours(self) -> _tp.Sequence[NodeBase]:
        return [self.fromNode, self.toNode]

    def getOtherNeighbour(self, neighbour: NodeBase) -> NodeBase:
        if neighbour not in self.getNeighbours():
            raise ValueError("`neighbour' is not one of our neighbours")

        if neighbour is self.fromNode:
            return self.toNode

        return self.fromNode

    def _getNeighbourIndices(self, nodesToIndices: _tp.Mapping["NodeBase", int]) -> _tp.Tuple[int, int, int]:
        fromIndex = nodesToIndices[self.fromNode]
        toIndex = nodesToIndices[self.toNode]
        return fromIndex, toIndex, Parameters.UNUSED_INDEX_VALUE

    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        return 2


class Pipe(TwoNeighboursBase):
    def _getNodeType(self) -> NodeType:
        return NodeType.PIPE


class Pump(TwoNeighboursBase):
    def _getNodeType(self) -> NodeType:
        return NodeType.PUMP

    def _getInputVariable(self) -> _tp.Optional[InputVariable]:
        return InputVariable(f"Mfr{self.name}")


@_dc.dataclass(eq=False)
class ThreeNeighboursBase(RealNodeBase, _abc.ABC):
    node1: NodeBase
    node2: NodeBase
    node3: NodeBase

    def getNeighbours(self) -> _tp.Sequence[NodeBase]:
        return [self.node1, self.node2, self.node3]

    def _getNeighbourIndices(self, nodesToIndices: _tp.Mapping["NodeBase", int]) -> _tp.Tuple[int, int, int]:
        node1Index = nodesToIndices[self.node1]
        node2Index = nodesToIndices[self.node2]
        node3Index = nodesToIndices[self.node3]
        neighbourIndices = (node1Index, node2Index, node3Index)
        return neighbourIndices

    def _getNumberOfOutputVariables(self) -> OutputVariableIndex:
        return 3


class Diverter(ThreeNeighboursBase):
    def _getNodeType(self) -> NodeType:
        return NodeType.DIVERTER

    def _getInputVariable(self) -> _tp.Optional[InputVariable]:
        return InputVariable(f"xFrac{self.name}")


class TeePiece(ThreeNeighboursBase):
    def _getNodeType(self) -> NodeType:
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
