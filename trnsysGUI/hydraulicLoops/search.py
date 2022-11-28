from __future__ import annotations

import typing as _tp

import trnsysGUI.common as _com
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.internalPiping
import trnsysGUI.massFlowSolver.export
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.singlePipePortItem as _spi


def getReachableConnections(
    port: _spi.SinglePipePortItem,
    ignoreConnections: _tp.Optional[_tp.Set[_spc.SinglePipeConnection]] = None,
) -> _tp.Set[_spc.SinglePipeConnection]:
    assert len(port.connectionList) <= 1

    portItems = {port}
    newPortItems, newConnections = _expandPortItemSetByOneLayer(portItems, ignoreConnections)
    while newPortItems != portItems:
        portItems = newPortItems
        newPortItems, newConnections = _expandPortItemSetByOneLayer(portItems, ignoreConnections)

    return newConnections


def _expandPortItemSetByOneLayer(
    portItems: set[_spi.SinglePipePortItem],
    ignoreConnections: _tp.Optional[set[_spc.SinglePipeConnection]] = None,
) -> _tp.Tuple[set[_spi.SinglePipePortItem], set[_spc.SinglePipeConnection]]:
    if ignoreConnections is None:
        ignoreConnections = set()

    connectedPortItems = [pi for pi in portItems if pi.connectionList]
    connections = [_com.getSingle(pi.connectionList) for pi in connectedPortItems]
    relevantConnections = {
        c for c in connections if isinstance(c, _spc.SinglePipeConnection) and c not in ignoreConnections
    }

    connectionPortItems = {p for c in relevantConnections for p in [c.fromPort, c.toPort]}

    internalPortItems = {mpi for p in portItems for mpi in getInternallyConnectedPortItems(p)}

    portItems = connectionPortItems | internalPortItems

    return portItems, relevantConnections


def getInternallyConnectedPortItems(
    port: _spi.SinglePipePortItem,
) -> _tp.Sequence[_spi.SinglePipePortItem]:
    contributor: trnsysGUI.internalPiping.HasInternalPiping = port.parent  # type: ignore[name-defined]
    internalPiping = contributor.getInternalPiping()

    graphicalPortItems = internalPiping.modelPortItemsToGraphicalPortItem
    nodes = internalPiping.nodes

    allModelPortItems = [n.getPortItems() for n in nodes]

    modelPortItem = internalPiping.getModelPortItem(port, _mfn.PortItemType.STANDARD)
    for modelPortItems in allModelPortItems:
        if modelPortItem in modelPortItems:
            internallyConnectedGraphicalPortItems = [graphicalPortItems[mpi] for mpi in modelPortItems]
            internallyConnectedSinglePortItems = [
                gpi for gpi in internallyConnectedGraphicalPortItems if isinstance(gpi, _spi.SinglePipePortItem)
            ]

            return internallyConnectedSinglePortItems

    raise AssertionError("Can't get here.")
