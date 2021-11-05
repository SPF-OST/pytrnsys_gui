# pylint: skip-file
# type: ignore

from __future__ import annotations

import math as _math
import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
from massFlowSolver import InternalPiping
from massFlowSolver.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.Connection import Connection
from trnsysGUI.PortItemBase import PortItemBase
from trnsysGUI.connection.segmentItemFactory import SegmentItemFactoryBase

if _tp.TYPE_CHECKING:
    pass


def calcDist(p1, p2):
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class DoublePipeConnection(Connection):
    def __init__(self, fromPort: PortItemBase, toPort: PortItemBase, segmentItemFactory: SegmentItemFactoryBase, parent):
        super().__init__(fromPort, toPort, segmentItemFactory, parent)

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.idGen.getTrnsysID())

    # Saving / Loading
    def encode(self):
        self.logger.debug("Encoding a connection")

        dct = {}
        dct[".__ConnectionDict__"] = True
        dct["fromPortId"] = self.fromPort.id
        dct["toPortId"] = self.toPort.id
        dct["name"] = self.displayName
        dct["id"] = self.id
        dct["connectionId"] = self.connId
        dct["trnsysId"] = self.trnsysId
        dct["childIds"] = self.childIds
        dct["groupName"] = self.groupName

        if len(self.segments) > 0:
            dct["labelPos"] = self.segments[0].label.pos().x(), self.segments[0].label.pos().y()
            dct["massFlowLabelPos"] = self.segments[0].labelMass.pos().x(), self.segments[0].labelMass.pos().y()
        else:
            defaultPos = self.fromPort.pos().x(), self.fromPort.pos().y()
            dct["labelPos"] = defaultPos
            dct["massFlowLabelPos"] = defaultPos

        corners = []
        for s in self.getCorners():
            cornerTupel = (s.pos().x(), s.pos().y())
            corners.append(cornerTupel)

        dct["segmentsCorners"] = corners

        dictName = "Connection-"

        return dictName, dct

    def decode(self, i):
        self.logger.debug("Loading a connection in Decoder")

        self.id = i["id"]
        self.connId = i["connectionId"]
        self.trnsysId = i["trnsysId"]
        self.childIds = i["childIds"]
        self.setName(i["name"])
        self.groupName = "defaultGroup"
        self.setConnToGroup(i["groupName"])

        if len(i["segmentsCorners"]) > 0:
            self.loadSegments(i["segmentsCorners"])

        self.setLabelPos(i["labelPos"])
        self.setMassLabelPos(i["massFlowLabelPos"])

    def getInternalPiping(self) -> InternalPiping:
        coldFromPort = ColdPortItem()
        coldToPort = ColdPortItem()
        coldPipe = _mfn.Pipe("Cold" + self.displayName, self.childIds[0], coldFromPort, coldToPort)
        ColdModelPortItemsToGraphicalPortItem = {coldFromPort: self.fromPort, coldToPort: self.toPort}

        hotFromPort = HotPortItem()
        hotToPort = HotPortItem()
        hotPipe = _mfn.Pipe("Hot" + self.displayName, self.childIds[1], hotFromPort, hotToPort)
        HotModelPortItemsToGraphicalPortItem = {hotFromPort: self.fromPort, hotToPort: self.toPort}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem
        return InternalPiping([coldPipe, hotPipe], ModelPortItemsToGraphicalPortItem)

    def getConnectedRealNode(self, portItem, internalPiping) -> _tp.Optional[_mfn.RealNodeBase]:
        assert portItem in internalPiping.modelPortItemsToGraphicalPortItem, "`portItem' doesn't belong to `internalPiping'"

        graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]

        assert graphicalPortItem in [self.fromPort, self.toPort], \
            "This connection is not connected to `graphicalPortItem'"

        blockItem: _mfs.MassFlowNetworkContributorMixin = graphicalPortItem.parent
        blockItemInternalPiping = blockItem.getInternalPiping()

        for startingNode in blockItemInternalPiping.openLoopsStartingNodes:
            realNodesAndPortItems = _mfn.getConnectedRealNodesAndPortItems(startingNode)
            for realNode in realNodesAndPortItems.realNodes:
                for candidatePortItem in [n for n in realNode.getNeighbours() if type(n) is type(portItem)]:
                    candidateGraphicalPortItem = blockItemInternalPiping.modelPortItemsToGraphicalPortItem[
                        candidatePortItem]
                    if candidateGraphicalPortItem == graphicalPortItem:
                        return realNode
        return None
