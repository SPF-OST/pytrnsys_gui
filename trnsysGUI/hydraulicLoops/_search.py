from __future__ import annotations

import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.singlePipePortItem as _spi

from . import _helpers


def getReachableConnections(
    port: _spi.SinglePipePortItem,  # type: ignore[name-defined]
    ignoreConnections: _tp.Set[_spc.SinglePipeConnection] = None,  # type: ignore[name-defined]
) -> _tp.Set[_spc.SinglePipeConnection]:  # type: ignore[name-defined]
    assert len(port.connectionList) <= 1

    portItems = {port}
    newPortItems, newConnections = _expandPortItemSetByOneLayer(portItems, ignoreConnections)
    while newPortItems != portItems:
        portItems = newPortItems
        newPortItems, newConnections = _expandPortItemSetByOneLayer(portItems, ignoreConnections)

    return newConnections


def _expandPortItemSetByOneLayer(
    portItems: set[_spi.SinglePipePortItem],  # type: ignore[name-defined]
    ignoreConnections: _tp.Optional[set[_spc.SinglePipeConnection]] = None,  # type: ignore[name-defined]
) -> _tp.Tuple[set[_spi.SinglePipePortItem], set[_spc.SinglePipeConnection]]:  # type: ignore[name-defined]
    if ignoreConnections is None:
        ignoreConnections = set()

    connectedPortItems = [pi for pi in portItems if pi.connectionList]
    connections = [_helpers.getSingle(pi.connectionList) for pi in connectedPortItems]
    relevantConnections = {
        c
        for c in connections
        if isinstance(c, _spc.SinglePipeConnection) and c not in ignoreConnections  # type: ignore[attr-defined]
    }

    connectionPortItems = {p for c in relevantConnections for p in [c.fromPort, c.toPort]}

    internalPortItems = {mpi for p in portItems for mpi in _getInternallyConnectedPortItems(p)}

    portItems = connectionPortItems | internalPortItems

    return portItems, relevantConnections


def _getInternallyConnectedPortItems(
    port: _spi.SinglePipePortItem,  # type: ignore[name-defined]
) -> _tp.Sequence[_spi.SinglePipePortItem]:  # type: ignore[name-defined]
    contributor: _mfs.MassFlowNetworkContributorMixin = port.parent  # type: ignore[name-defined]
    internalPiping = contributor.getInternalPiping()

    graphicalPortItems = internalPiping.modelPortItemsToGraphicalPortItem
    startingNodes = internalPiping.openLoopsStartingNodes

    allInternallyConnectedModelPortItems = [_mfn.getConnectedRealNodesAndPortItems(sn).portItems for sn in startingNodes]

    allInternallyConnectedPortItems = []
    for internallyConnectedModelPortItems in allInternallyConnectedModelPortItems:
        internallyConnectedPortItems = []
        for modelPortItem in internallyConnectedModelPortItems:
            graphicalPortItem = graphicalPortItems[modelPortItem]
            if not isinstance(graphicalPortItem, _spi.SinglePipePortItem):
                continue

            internallyConnectedPortItems.append(graphicalPortItem)

        allInternallyConnectedPortItems.append(internallyConnectedPortItems)

    allIncidentInternallyConnectedPortItems = [pis for pis in allInternallyConnectedPortItems if port in pis]

    assert len(allIncidentInternallyConnectedPortItems) == 1

    incidentInternallyConnectedPortItems = allIncidentInternallyConnectedPortItems[0]

    return incidentInternallyConnectedPortItems


def _getSingle(
    connectionList: _tp.Sequence[_spc.SinglePipeConnection],  # type: ignore[name-defined]
) -> _spc.SinglePipeConnection:  # type: ignore[name-defined]
    assert len(connectionList) == 1
    return connectionList[0]
