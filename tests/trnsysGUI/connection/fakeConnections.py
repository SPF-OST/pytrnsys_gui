import typing as _tp
import logging as _log
from PyQt5 import QtCore as _qtc

import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.internalPiping as _ip
import trnsysGUI.segments.Node as _node


class StrictMockBase:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _StrictMockWithMethods(StrictMockBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def clearConn(self):
        pass


class FakePort(StrictMockBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x = 0
        self.y = 0

    def scenePos(self):
        return _qtc.QPointF(self.x, self.y)


def createSimpleDoublePipeConnectionMock(
        displayName: str, fromPort=StrictMockBase(), toPort=StrictMockBase()
) -> _dpc.DoublePipeConnection:
    coldInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
    coldOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
    coldModelPipe = _mfn.Pipe(coldInput, coldOutput, "Cold")

    hotInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
    hotOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
    hotModelPipe = _mfn.Pipe(hotInput, hotOutput, "Hot")

    def getInternalPiping() -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {coldModelPipe.fromPort: toPort, coldModelPipe.toPort: fromPort}
        hotModelPortItemsToGraphicalPortItem = {hotModelPipe.fromPort: fromPort, hotModelPipe.toPort: toPort}
        modelPortItemsToGraphicalPortItem = (
                coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
        )
        return _ip.InternalPiping([coldModelPipe, hotModelPipe], modelPortItemsToGraphicalPortItem)

    mock = StrictMockBase(
        displayName=displayName,
        getDisplayName=lambda: displayName,
        fromPort=fromPort,
        toPort=toPort,
        _hotPipe=hotModelPipe,
        _coldPipe=coldModelPipe,
        getInternalPiping=getInternalPiping,
        hasDdckPlaceHolders=lambda: False,
        shallRenameOutputTemperaturesInHydraulicFile=lambda: False,
    )

    return _tp.cast(_dpc.DoublePipeConnection, mock)


def createFullDoublePipeConnectionMock(
        displayName: str, fromPort=FakePort(), toPort=FakePort()
) -> _dpc.DoublePipeConnection:

    fromPort.x = 0
    fromPort.y = 0
    toPort.x = 10
    toPort.y = 10

    coldInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
    coldOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
    coldModelPipe = _mfn.Pipe(coldInput, coldOutput, "Cold")

    hotInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
    hotOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
    hotModelPipe = _mfn.Pipe(hotInput, hotOutput, "Hot")

    def getInternalPiping() -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {coldModelPipe.fromPort: toPort, coldModelPipe.toPort: fromPort}
        hotModelPortItemsToGraphicalPortItem = {hotModelPipe.fromPort: fromPort, hotModelPipe.toPort: toPort}
        modelPortItemsToGraphicalPortItem = (
                coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
        )
        return _ip.InternalPiping([coldModelPipe, hotModelPipe], modelPortItemsToGraphicalPortItem)

    mock = _StrictMockWithMethods(
        startNode=_node.Node(),
        endNode=_node.Node(),
        logger=_log.getLogger("root"),
        segments=[],
        displayName=displayName,
        getDisplayName=lambda: displayName,
        fromPort=fromPort,
        toPort=toPort,
        _hotPipe=hotModelPipe,
        _coldPipe=coldModelPipe,
        getInternalPiping=getInternalPiping,
        hasDdckPlaceHolders=lambda: False,
        shallRenameOutputTemperaturesInHydraulicFile=lambda: False,
    )

    return _tp.cast(_dpc.DoublePipeConnection, mock)
