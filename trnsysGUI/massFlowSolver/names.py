import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


def getMassFlowVariableName(
    hasInternalPiping: _ip.HasInternalPiping, node: _mfn.Node, portItem: _mfn.PortItem
) -> str:
    if portItem not in node.getPortItems():
        raise ValueError("`portItem` not one of `node`'s port items.")

    postfix = _getPostfix(node, portItem)

    displayName = hasInternalPiping.getDisplayName()

    nodeNameOrEmpty = node.name or ""

    return f"M{displayName}{nodeNameOrEmpty}_{postfix}"


def getCanonicalMassFlowVariableName(
    hasInternalPiping: _ip.HasInternalPiping, pipe: _mfn.Pipe
) -> str:
    pipeNameOrEmpty = pipe.name or ""
    return f"M{hasInternalPiping.getDisplayName()}{pipeNameOrEmpty}"


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
