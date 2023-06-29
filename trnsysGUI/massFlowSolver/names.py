import typing as _tp

import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


# These constants are defined in `head.ddck`
ABSOLUTE_TOLERANCE_NAME = "mfrSolverAbsTol"
RELATIVE_TOLERANCE_NAME = "mfrSolverRelTol"
TOLERANCE_SWITCHING_THRESHOLD_NAME = "mfrTolSwitchThreshold"


def getMassFlowVariableName(hasInternalPiping: _ip.HasInternalPiping, node: _mfn.Node, portItem: _mfn.PortItem) -> str:
    if portItem not in node.getPortItems():
        raise ValueError("`portItem` not one of `node`'s port items.")

    displayName = hasInternalPiping.getDisplayName()
    nodeNameOrEmpty = node.name or ""
    massFlowVariableNameWithoutPostfix = f"M{displayName}{nodeNameOrEmpty}"

    postfix = _getPostfix(node, portItem)
    if not postfix:
        return massFlowVariableNameWithoutPostfix

    return f"{massFlowVariableNameWithoutPostfix}_{postfix}"


def getCanonicalMassFlowVariableName(*, componentDisplayName: str, pipeName: _tp.Optional[str]) -> str:
    pipeNameOrEmpty = pipeName or ""
    return f"M{componentDisplayName}{pipeNameOrEmpty}"


def _getPostfix(node: _mfn.Node, portItem: _mfn.PortItem) -> _tp.Optional[str]:
    portItems = node.getPortItemsRelevantToOutputEquations()
    if len(portItems) == 1:
        return None

    postfixes = "ABC"

    for candidatePortItem, postfix in zip(portItems, postfixes):
        if candidatePortItem == portItem:
            return postfix

    raise ValueError("`portItem` not one of `node`'s port items.")


def getInputVariableName(hasInternalPiping: _ip.HasInternalPiping, node: _mfn.Node) -> str:
    prefix = node.getInputVariablePrefix()
    nodeNameOrEmtpy = node.name or ""
    displayName = hasInternalPiping.getDisplayName()
    return f"{prefix}{displayName}{nodeNameOrEmtpy}"
