import typing as _tp

import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn

# These constants are defined in `head.ddck`
ABSOLUTE_TOLERANCE_NAME = "mfrSolverAbsTol"
RELATIVE_TOLERANCE_NAME = "mfrSolverRelTol"
TOLERANCE_SWITCHING_THRESHOLD_NAME = "mfrTolSwitchThreshold"


def getMassFlowVariableName(displayName: str, node: _mfn.Node, portItem: _mfn.PortItem) -> str:
    if portItem not in node.getPortItems():
        raise ValueError("`portItem` not one of `node`'s port items.")

    postfix = _getPostfix(node, portItem)

    nodeNameOrEmpty = node.name or ""

    return f"M{displayName}{nodeNameOrEmpty}_{postfix}"


def getCanonicalMassFlowVariableName(*, componentDisplayName: str, pipeName: _tp.Optional[str]) -> str:
    pipeNameOrEmpty = pipeName or ""
    return f"M{componentDisplayName}{pipeNameOrEmpty}"


def _getPostfix(node: _mfn.Node, portItem: _mfn.PortItem) -> str:
    postfixes = "ABC"
    portItems = node.getPortItems()

    for candidatePortItem, postfix in zip(portItems, postfixes):
        if candidatePortItem == portItem:
            return postfix

    raise ValueError("`portItem` not one of `node`'s port items.")


def getInputVariableName(hasInternalPiping: _ip.HasInternalPiping, node: _mfn.Node) -> str:
    prefix = node.getInputVariablePrefix()
    nodeNameOrEmtpy = node.name or ""
    displayName = hasInternalPiping.getDisplayName()
    return f"{prefix}{displayName}{nodeNameOrEmtpy}"
