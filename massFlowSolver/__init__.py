import dataclasses as _dc
import typing as _tp

import trnsysGUI.PortItemBase as _pi
from massFlowSolver import networkModel as _mfn


@_dc.dataclass
class InternalPiping:
    openLoopsStartingNodes: _tp.Sequence[_mfn.RealNodeBase]
    modelPortItemsToGraphicalPortItem: _tp.Mapping[_mfn.PortItem, _pi.PortItemBase]


@_dc.dataclass
class _OpenLoop:
    nodes: _tp.Sequence[_mfn.NodeBase]


class MassFlowNetworkContributorMixin:
    def getInternalPiping(self) -> InternalPiping:
        raise NotImplementedError()

    def exportParametersFlowSolver(self, descConnLength):
        openLoops, allNodesToIndices = self._getOpenLoopsAndNodeToIndices()

        allParameters = []
        for openLoop in openLoops:
            realNodes = [n for n in openLoop.nodes if isinstance(n, _mfn.RealNodeBase)]
            parameters = [rn.serialize(allNodesToIndices).parameters for rn in realNodes]
            allParameters.extend(parameters)

        return "\n".join(parameters.toString(descConnLength) for parameters in allParameters) + "\n"

    def exportInputsFlowSolver(self):
        openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()

        allInputVariables = []
        for openLoop in openLoops:
            inputVariables = [n.serialize(nodesToIndices).inputVariable for n in openLoop.nodes if isinstance(n, _mfn.RealNodeBase)]
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
            for node in openLoop.nodes:
                if not isinstance(node, _mfn.RealNodeBase):
                    continue
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
            connectedNodes = _mfn.getConnectedNodes(startingNode)
            openLoops.append(_OpenLoop(connectedNodes))

            portItems = [n for n in connectedNodes if isinstance(n, _mfn.PortItem)]
            realNodes = [n for n in connectedNodes if isinstance(n, _mfn.RealNodeBase)]

            portItemsToIndices = {}
            for portItem in portItems:
                connectedRealNode = self._getConnectedRealNode(portItem, internalPiping)  # find connected element
                if not connectedRealNode:
                    raise AssertionError("Hydraulics not connected.")
                portItemsToIndices[portItem] = connectedRealNode.trnsysId  # BlockID
            realNodesToIndices = {n: n.trnsysId for n in realNodes}  # ConnectionID's
            nodesToIndices = portItemsToIndices | realNodesToIndices

            allNodesToIndices |= nodesToIndices
        return openLoops, allNodesToIndices

    def _getConnectedRealNode(self, portItem: _mfn.PortItem, internalPiping: InternalPiping) -> _tp.Optional[_mfn.RealNodeBase]:
        raise NotImplementedError()
