import abc as _abc
import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
from massFlowSolver import InternalPiping
from massFlowSolver.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.SegmentItemBase import SegmentItemBase  # type: ignore[attr-defined]


class PipeModel(_abc.ABC):
    @_abc.abstractmethod
    def getInternalPiping(self) -> InternalPiping:
        raise NotImplementedError()

    def getConnectedRealNode(self, portItem: _mfn.PortItem, internalPiping: _mfs.InternalPiping) -> _tp.Optional[_mfn.RealNodeBase]:
        raise NotImplementedError()

    def getDecoder(self):
        raise NotImplementedError()


class SinglePipeModel(PipeModel):

    def getInternalPiping(self, connection) -> InternalPiping:
        fromPort = _mfn.PortItem()
        toPort = _mfn.PortItem()

        pipe = _mfn.Pipe(connection.displayName, connection.trnsysId, fromPort, toPort)
        return InternalPiping([pipe], {fromPort: connection.fromPort, toPort: connection.toPort})

    def getConnectedRealNode(self, portItem, internalPiping, connection) -> _tp.Optional[_mfn.RealNodeBase]:
        assert portItem in internalPiping.modelPortItemsToGraphicalPortItem, "`portItem' doesn't belong to `internalPiping'"

        graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]

        assert graphicalPortItem in [connection.fromPort, connection.toPort],\
            "This connection is not connected to `graphicalPortItem'"

        blockItem: _mfs.MassFlowNetworkContributorMixin = graphicalPortItem.parent
        blockItemInternalPiping = blockItem.getInternalPiping()

        for startingNode in blockItemInternalPiping.openLoopsStartingNodes:
            realNodesAndPortItems = _mfn.getConnectedRealNodesAndPortItems(startingNode)
            for realNode in realNodesAndPortItems.realNodes:
                for portItem in [n for n in realNode.getNeighbours() if isinstance(n, _mfn.PortItem)]:
                    candidateGraphicalPortItem = blockItemInternalPiping.modelPortItemsToGraphicalPortItem[portItem]
                    if candidateGraphicalPortItem == graphicalPortItem:
                        return realNode
        return None


class DoublePipeModel(PipeModel):

    def getInternalPiping(self, connection) -> InternalPiping:
        coldFromPort = ColdPortItem()
        coldToPort = ColdPortItem()
        coldPipe = _mfn.Pipe("Cold"+connection.displayName, connection.childIds[0], coldFromPort, coldToPort)
        ColdModelPortItemsToGraphicalPortItem = {coldFromPort: connection.fromPort, coldToPort: connection.toPort}

        hotFromPort = HotPortItem()
        hotToPort = HotPortItem()
        hotPipe = _mfn.Pipe("Hot"+connection.displayName, connection.childIds[1], hotFromPort, hotToPort)
        HotModelPortItemsToGraphicalPortItem = {hotFromPort: connection.fromPort, hotToPort: connection.toPort}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem
        return InternalPiping([coldPipe, hotPipe], ModelPortItemsToGraphicalPortItem)

    def getConnectedRealNode(self, portItem, internalPiping, connection) -> _tp.Optional[_mfn.RealNodeBase]:
        assert portItem in internalPiping.modelPortItemsToGraphicalPortItem, "`portItem' doesn't belong to `internalPiping'"

        graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]

        assert graphicalPortItem in [connection.fromPort, connection.toPort], \
            "This connection is not connected to `graphicalPortItem'"

        blockItem: _mfs.MassFlowNetworkContributorMixin = graphicalPortItem.parent
        blockItemInternalPiping = blockItem.getInternalPiping()

        for startingNode in blockItemInternalPiping.openLoopsStartingNodes:
            realNodesAndPortItems = _mfn.getConnectedRealNodesAndPortItems(startingNode)
            for realNode in realNodesAndPortItems.realNodes:
                for candidatePortItem in [n for n in realNode.getNeighbours() if type(n) is type(portItem)]:
                    candidateGraphicalPortItem = blockItemInternalPiping.modelPortItemsToGraphicalPortItem[candidatePortItem]
                    if candidateGraphicalPortItem == graphicalPortItem:
                        return realNode
        return None