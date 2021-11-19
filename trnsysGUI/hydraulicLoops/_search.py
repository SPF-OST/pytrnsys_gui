from __future__ import annotations

import typing as _tp

import massFlowSolver as _mfs
from massFlowSolver import networkModel as _mfn
import trnsysGUI.PortItem as _pi

if _tp.TYPE_CHECKING:
    import trnsysGUI.Connection as _conn


def getReachableConnections(port: _pi.PortItem) -> set[_conn.Connection]:  # type: ignore[name-defined]
    assert len(port.connectionList) <= 1

    portItems = {port}
    newPortItems, newConnections = _expandPortItemSetByOneLayer(portItems)
    while newPortItems != portItems:
        portItems = newPortItems
        newPortItems, newConnections = _expandPortItemSetByOneLayer(portItems)

    return newConnections


def _expandPortItemSetByOneLayer(
    portItems: set[_pi.PortItem],  # type: ignore[name-defined]
) -> _tp.Tuple[set[_pi.PortItem], set[_conn.Connection]]:  # type: ignore[name-defined]
    connections = {_getSingleConnection(p) for p in portItems if p.connectionList}
    connectionPortItems = {p for c in connections for p in [c.fromPort, c.toPort]}

    internalPortItems = {mpi for p in portItems for mpi in _getInternallyConnectedPortItems(p)}

    portItems = connectionPortItems | internalPortItems

    return portItems, connections


def _getInternallyConnectedPortItems(port: _pi.PortItem) -> _tp.Sequence[_pi.PortItem]:  # type: ignore[name-defined]
    contributor: _mfs.MassFlowNetworkContributorMixin = port.parent  # type: ignore[name-defined]
    internalPiping = contributor.getInternalPiping()

    graphicalPortItems = internalPiping.modelPortItemsToGraphicalPortItem
    startingNodes = internalPiping.openLoopsStartingNodes

    allInternallyConnectedModelPortItems = [_mfn.getConnectedRealNodesAndPortItems(sn).portItems for sn in startingNodes]

    allInternallyConnectedPortItems = [
        [graphicalPortItems[mpi] for mpi in mpis] for mpis in allInternallyConnectedModelPortItems
    ]

    allIncidentInternallyConnectedPortItems = [pis for pis in allInternallyConnectedPortItems if port in pis]

    assert len(allIncidentInternallyConnectedPortItems) == 1
    return allIncidentInternallyConnectedPortItems[0]


def _getSingleConnection(portItem: _pi.PortItem) -> _conn.Connection:  # type: ignore[name-defined]
    assert len(portItem.connectionList) == 1
    return portItem.connectionList[0]
