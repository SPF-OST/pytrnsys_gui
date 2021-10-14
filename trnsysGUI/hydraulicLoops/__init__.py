# pylint: skip-file

from __future__ import annotations

__all__ = ["getOrCreateHydraulicLoop", "showHydraulicLoopDialog"]

import typing as _tp

import trnsysGUI.PortItem as _pi

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn

from . import _gui
from . import _model


def getOrCreateHydraulicLoop(
    fromPort: _pi.PortItem, toPort: _pi.PortItem  # type: ignore[name-defined]
) -> "_model.HydraulicLoop":
    fromPortConnections = _getReachableConnections(fromPort)
    toPortConnections = _getReachableConnections(toPort)

    water = _model.PredefinedFluids.WATER
    connections = list(fromPortConnections | toPortConnections)

    modelConnections = [
        _model.Connection(c.displayName, 10, 500, c)
        for c in connections
    ]

    return _model.HydraulicLoop("loop", water, modelConnections)


def _getReachableConnections(port: _pi.PortItem) -> set[_conn.Connection]:  # type: ignore[name-defined]
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


def showHydraulicLoopDialog(fromPort: _pi.PortItem, toPort: _pi.PortItem) -> None:  # type: ignore[name-defined]
    hydraulicLoop = getOrCreateHydraulicLoop(fromPort, toPort)

    okedOrCancelled = _gui.HydraulicLoopDialog.showDialog(hydraulicLoop)
    if okedOrCancelled == "cancelled":
        return

    _applyModel(hydraulicLoop)


def _applyModel(hydraulicLoop: _model.HydraulicLoop) -> None:
    pass
