import dataclasses as _dc
import typing as _tp

import trnsysGUI.PortItemBase as _pi
from massFlowSolver import networkModel as _mfn


@_dc.dataclass
class PortItemAndAdjacentRealNode:
    portItem: _mfn.PortItem
    realNode: _mfn.RealNodeBase


@_dc.dataclass
class InternalPiping:
    openLoopsStartingNodes: _tp.Sequence[_mfn.RealNodeBase]
    modelPortItemsToGraphicalPortItem: _tp.Mapping[_mfn.PortItem, _pi.PortItemBase]

    def getPortItemsAndAdjacentRealNodeForGraphicalPortItem(
        self, graphicalPortItem: _pi.PortItemBase
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


@_dc.dataclass
class _OpenLoop:
    realNodes: _tp.Sequence[_mfn.RealNodeBase]


class MassFlowNetworkContributorMixin:
    def getInternalPiping(self) -> InternalPiping:
        raise NotImplementedError()

    def exportParametersFlowSolver(self, descConnLength):
        openLoops, allNodesToIndices = self._getOpenLoopsAndNodeToIndices()

        allParameters = []
        for openLoop in openLoops:
            parameters = [rn.serialize(allNodesToIndices).parameters for rn in openLoop.realNodes]
            allParameters.extend(parameters)

        return "\n".join(parameters.toString(descConnLength) for parameters in allParameters) + "\n"

    def exportInputsFlowSolver(self):
        openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()

        allInputVariables = []
        for openLoop in openLoops:
            inputVariables = [
                n.serialize(nodesToIndices).inputVariable for n in openLoop.realNodes
            ]
            allInputVariables.extend(inputVariables)

        line = ""
        for inputVariable in allInputVariables:
            if not inputVariable:
                line += f"{_mfn.InputVariable.UNDEFINED_INPUT_VARIABLE_VALUE} "
            else:
                line += f"{inputVariable.name} "

        return line, len(allInputVariables)

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()

        lines = []
        nodeIndex = 0
        for openLoop in openLoops:
            for node in openLoop.realNodes:
                outputVariables = node.serialize(nodesToIndices).outputVariables
                for variableIndex, outputVariable in enumerate(outputVariables):
                    if not outputVariable:
                        continue

                    index = equationNumber + nodeIndex * _mfn.MAX_N_OUTPUT_VARIABLES_PER_NODE + variableIndex
                    line = f"{outputVariable.name}=[{simulationUnit},{index}]"
                    lines.append(line)
                nodeIndex += 1

        joinedLines = "\n".join(lines) + "\n"
        nLinesGenerated = len(lines)
        nextEquationNumber = equationNumber + nodeIndex * _mfn.MAX_N_OUTPUT_VARIABLES_PER_NODE

        return joinedLines, nextEquationNumber, nLinesGenerated

    def _getOpenLoopsAndNodeToIndices(self) -> _tp.Tuple[_tp.Sequence[_OpenLoop], _tp.Mapping[_mfn.NodeBase, int]]:
        internalPiping = self.getInternalPiping()
        allNodesToIndices = {}
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
            nodesToIndices = portItemsToIndices | realNodesToIndices

            allNodesToIndices |= nodesToIndices
        return openLoops, allNodesToIndices
