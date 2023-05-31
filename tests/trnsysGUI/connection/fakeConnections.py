import typing as _tp
import logging as _log
from PyQt5 import QtCore as _qtc

import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.internalPiping as _ip
import trnsysGUI.segments.Node as _node
import trnsysGUI.connection.singlePipeConnection as _spc


class StrictMockBase:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _StrictMockWithMethods(StrictMockBase):
    def __init__(self, fromPort=None, toPort=None, **kwargs):
        super().__init__(**kwargs)
        self.fromPort = fromPort
        self.toPort = toPort

    def clearConn(self):
        # This method currently does not need to do anything in the tests.
        pass


class FakePort(StrictMockBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.xPos = 0
        self.yPos = 0

    def scenePos(self):
        return _qtc.QPointF(self.xPos, self.yPos)


def createSimpleDoublePipeConnectionMock(displayName: str, fromPort=None, toPort=None) -> _dpc.DoublePipeConnection:
    coldModelPipe, hotModelPipe = getHotAndColdPipes()

    def getInternalPiping() -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {coldModelPipe.fromPort: toPort, coldModelPipe.toPort: fromPort}
        hotModelPortItemsToGraphicalPortItem = {hotModelPipe.fromPort: fromPort, hotModelPipe.toPort: toPort}
        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
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


def getHotAndColdPipes():
    coldInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
    coldOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
    coldModelPipe = _mfn.Pipe(coldInput, coldOutput, "Cold")

    hotInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
    hotOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
    hotModelPipe = _mfn.Pipe(hotInput, hotOutput, "Hot")

    return coldModelPipe, hotModelPipe


def createFullDoublePipeConnectionMock(displayName: str, fromPort=None, toPort=None) -> _dpc.DoublePipeConnection:
    if not fromPort:
        fromPort = FakePort()

    if not toPort:
        toPort = FakePort()

    fromPort.xPos = 0
    fromPort.yPos = 0
    toPort.xPos = 10
    toPort.yPos = 10

    coldModelPipe, hotModelPipe = getHotAndColdPipes()

    mock = _StrictMockWithMethods(
        startNode=_node.Node(),  # type: ignore[attr-defined]
        endNode=_node.Node(),  # type: ignore[attr-defined]
        logger=_log.getLogger("root"),
        segments=[],
        displayName=displayName,
        getDisplayName=lambda: displayName,
        fromPort=fromPort,
        toPort=toPort,
        _hotPipe=hotModelPipe,
        _coldPipe=coldModelPipe,
        hasDdckPlaceHolders=lambda: False,
        shallRenameOutputTemperaturesInHydraulicFile=lambda: False,
    )

    return _tp.cast(_dpc.DoublePipeConnection, mock)


def createSimpleSPConnectionMock(
    displayName: str, fromPort=StrictMockBase(), toPort=StrictMockBase()
) -> _spc.SinglePipeConnection:
    modelPipe = _mfn.Pipe(
        _mfn.PortItem("In", _mfn.PortItemDirection.INPUT), _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
    )

    def getInternalPiping() -> _ip.InternalPiping:
        return _ip.InternalPiping([modelPipe], {modelPipe.fromPort: fromPort, modelPipe.toPort: toPort})

    def getModelPipe(portItemType: _mfn.PortItemType) -> _mfn.Pipe:
        assert portItemType == _mfn.PortItemType.STANDARD

        return modelPipe

    mock = StrictMockBase(
        displayName=displayName,
        getDisplayName=lambda: displayName,
        fromPort=fromPort,
        toPort=toPort,
        modelPipe=modelPipe,
        getModelPipe=getModelPipe,
        getInternalPiping=getInternalPiping,
        hasDdckPlaceHolders=lambda: False,
        shallRenameOutputTemperaturesInHydraulicFile=lambda: False,
    )

    return _tp.cast(_spc.SinglePipeConnection, mock)
