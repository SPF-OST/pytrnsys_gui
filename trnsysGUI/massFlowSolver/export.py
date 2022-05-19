import typing as _tp

import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.massFlowSolver.names as _mnames


def exportInputsFlowSolver(hasInternalPiping: _ip.HasInternalPiping) -> _tp.Tuple[str, int]:
    internalPiping = hasInternalPiping.getInternalPiping()
    nodes = internalPiping.nodes

    line = ""
    for node in nodes:
        if not node.hasInput():
            line += f"{_mfn.InputVariable.UNDEFINED_INPUT_VARIABLE_VALUE} "
        else:
            inputVariableName = _mnames.getInputVariableName(hasInternalPiping, node)
            line += f"{inputVariableName} "

    return line, len(nodes)


def exportOutputsFlowSolver(
    hasInternalPiping: _ip.HasInternalPiping, equationNumber: int, simulationUnit: int
) -> _tp.Tuple[str, int, int]:
    internalPiping = hasInternalPiping.getInternalPiping()

    lines = _getOutputLines(hasInternalPiping, equationNumber, simulationUnit)

    joinedLines = "\n".join(lines) + "\n"
    nLinesGenerated = len(lines)
    nextEquationNumber = equationNumber + len(internalPiping.nodes) * _mfn.MAX_N_OUTPUT_VARIABLES_PER_NODE

    return joinedLines, nextEquationNumber, nLinesGenerated


def _getOutputLines(
    hasInternalPiping: _ip.HasInternalPiping, equationNumber: int, simulationUnit: int
) -> _tp.Sequence[str]:
    internalPiping = hasInternalPiping.getInternalPiping()
    nodes = internalPiping.nodes

    lines = []
    for nodeIndex, node in enumerate(nodes):
        portItems = node.getPortItems()
        for variableIndex, portItem in enumerate(portItems):
            outputVariable = _mnames.getMassFlowVariableName(hasInternalPiping, node, portItem)
            index = equationNumber + nodeIndex * _mfn.MAX_N_OUTPUT_VARIABLES_PER_NODE + variableIndex
            line = f"{outputVariable}=[{simulationUnit},{index}]"
            lines.append(line)

    return lines
