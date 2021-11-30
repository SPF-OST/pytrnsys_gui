from __future__ import annotations

import typing as _tp

import massFlowSolver as _mfs
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.singlePipePortItem as _spi
from massFlowSolver import networkModel as _mfn


def getReachableConnections(
    port: _spi.SinglePipePortItem,  # type: ignore[name-defined]
) -> set[_spc.SinglePipeConnection]:  # type: ignore[name-defined]
    assert len(port.connectionList) <= 1

    portItems = {port}
    newPortItems, newConnections = _expandPortItemSetByOneLayer(portItems)
    while newPortItems != portItems:
        portItems = newPortItems
        newPortItems, newConnections = _expandPortItemSetByOneLayer(portItems)

    return newConnections


def _expandPortItemSetByOneLayer(
    portItems: set[_spi.SinglePipePortItem],  # type: ignore[name-defined]
) -> _tp.Tuple[set[_spi.SinglePipePortItem], set[_spc.SinglePipeConnection]]:  # type: ignore[name-defined]
    connections = set()
    for portItem in portItems:
        if not portItem.connectionList:
            continue

        connection = _getSingle(portItem.connectionList)
        if not isinstance(connection, _spc.SinglePipeConnection):  # type: ignore[attr-defined]
            continue

        connections.add(connection)

    connectionPortItems = {p for c in connections for p in [c.fromPort, c.toPort]}

    internalPortItems = {mpi for p in portItems for mpi in _getInternallyConnectedPortItems(p)}

    portItems = connectionPortItems | internalPortItems

    return portItems, connections


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
