import dataclasses as _dc
import typing as _tp

import trnsysGUI.PortItemBase as _pi
from trnsysGUI.massFlowSolver import networkModel as _mfn


@_dc.dataclass
class PortItemAndAdjacentRealNode:
    portItem: _mfn.PortItem
    realNode: _mfn.RealNodeBase


@_dc.dataclass
class InternalPiping:
    openLoopsStartingNodes: _tp.Sequence[_mfn.RealNodeBase]
    modelPortItemsToGraphicalPortItem: _tp.Mapping[_mfn.PortItem, _pi.PortItemBase]  # type: ignore[name-defined]

    def getPortItemsAndAdjacentRealNodeForGraphicalPortItem(
        self, graphicalPortItem: _pi.PortItemBase  # type: ignore[name-defined]
    ) -> _tp.Sequence[PortItemAndAdjacentRealNode]:
        if graphicalPortItem not in self.modelPortItemsToGraphicalPortItem.values():
            raise ValueError("The graphical port item is not part of this internal piping.")

        portItemsAndAdjacentRealNode = []
        for startingNode in self.openLoopsStartingNodes:
            realNodesAndPortItems = _mfn.getConnectedRealNodesAndPortItems(startingNode)
            for realNode in realNodesAndPortItems.realNodes:
                for candidatePortItem in [n for n in realNode.getNeighbours() if isinstance(n, _mfn.PortItem)]:
                    candidateGraphicalPortItem = self.modelPortItemsToGraphicalPortItem[candidatePortItem]
                    if candidateGraphicalPortItem == graphicalPortItem:
                        portItem = candidatePortItem
                        portItemAndAdjacentRealNode = PortItemAndAdjacentRealNode(portItem, realNode)

                        portItemsAndAdjacentRealNode.append(portItemAndAdjacentRealNode)
        return portItemsAndAdjacentRealNode

    def getAllRealNodes(self) -> _tp.Sequence[_mfn.RealNodeBase]:
        allRealNodes: _tp.List[_mfn.RealNodeBase] = []
        for startingNode in self.openLoopsStartingNodes:
            visitedNodes = {startingNode}
            stack = [startingNode]
            while stack:
                currentNode = stack.pop()
                unvisitedNodes = [
                    n for n in currentNode.getNeighbours() if n not in visitedNodes and isinstance(n, _mfn.RealNodeBase)
                ]
                visitedNodes.update(unvisitedNodes)
                stack.extend(unvisitedNodes)

            allRealNodes.extend(visitedNodes)

        return allRealNodes


@_dc.dataclass
class _OpenLoop:
    realNodes: _tp.Sequence[_mfn.RealNodeBase]


class MassFlowNetworkContributorMixin:
    def getInternalPiping(self) -> InternalPiping:
        raise NotImplementedError()

    def exportInputsFlowSolver(self):
        openLoops, _ = self._getOpenLoopsAndNodeToIndices()

        allInputVariables = []
        for openLoop in openLoops:
            inputVariables = [n.getInputVariable() for n in openLoop.realNodes]
            allInputVariables.extend(inputVariables)

        line = ""
        for inputVariable in allInputVariables:
            if not inputVariable:
                line += f"{_mfn.InputVariable.UNDEFINED_INPUT_VARIABLE_VALUE} "
            else:
                line += f"{inputVariable.name} "

        return line, len(allInputVariables)

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):  # pylint: disable=unused-argument
        openLoops, _ = self._getOpenLoopsAndNodeToIndices()

        realNodes = [n for l in openLoops for n in l.realNodes]

        lines = self._getOutputLines(realNodes, equationNumber, simulationUnit)

        joinedLines = "\n".join(lines) + "\n"
        nLinesGenerated = len(lines)
        nextEquationNumber = equationNumber + len(realNodes) * _mfn.MAX_N_OUTPUT_VARIABLES_PER_NODE

        return joinedLines, nextEquationNumber, nLinesGenerated

    @staticmethod
    def _getOutputLines(realNodes: _tp.Sequence[_mfn.RealNodeBase], equationNumber, simulationUnit):
        lines = []
        for nodeIndex, node in enumerate(realNodes):
            outputVariables = node.getOutputVariables()
            for variableIndex, outputVariable in enumerate(outputVariables):
                if not outputVariable:
                    continue

                index = equationNumber + nodeIndex * _mfn.MAX_N_OUTPUT_VARIABLES_PER_NODE + variableIndex
                line = f"{outputVariable.name}=[{simulationUnit},{index}]"
                lines.append(line)
        return lines

    def _getOpenLoopsAndNodeToIndices(self) -> _tp.Tuple[_tp.Sequence[_OpenLoop], _tp.Mapping[_mfn.NodeBase, int]]:
        internalPiping = self.getInternalPiping()
        allNodesToIndices: _tp.Dict[_mfn.NodeBase, int] = {}
        openLoops = []
        for startingNode in internalPiping.openLoopsStartingNodes:
            realNodesAndPortItems = _mfn.getConnectedRealNodesAndPortItems(startingNode)
            realNodes = realNodesAndPortItems.realNodes
            portItems = realNodesAndPortItems.portItems

            openLoops.append(_OpenLoop(realNodes))

            portItemsToIndices = {}
            for portItem in portItems:
                graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]
                connectedRealNode = graphicalPortItem.getConnectedRealNode(portItem, self)
                if not connectedRealNode:
                    raise AssertionError("Hydraulics not connected.")
                portItemsToIndices[portItem] = connectedRealNode.trnsysId
            realNodesToIndices = {n: n.trnsysId for n in realNodes}

            # Jump through some hoops to make `mypy` type check this
            # (see https://github.com/python/mypy/issues/1114)
            nodesAndIndex = [
                *list(portItemsToIndices.items()),
                *list(realNodesToIndices.items()),
            ]
            nodesToIndices = dict(nodesAndIndex)

            allNodesToIndices |= nodesToIndices
        return openLoops, allNodesToIndices
