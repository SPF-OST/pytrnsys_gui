import unittest.mock as _m

import trnsysGUI.connection.getNiceConnector as _gnc
from trnsysGUI import CornerItem as _ci

from . import fakeConnections as _fc

spConnection = _fc.createSimpleSPConnectionMock("spConnectionName")


class FakeSegmentItem(_fc.StrictMockBase):
    def __init__(self, startNode, endNode, connection, **kwargs):
        super().__init__(**kwargs)
        self.startNode = startNode
        self.endNode = endNode
        self.connection = connection

    def setLine(self, point1, point2):
        pass


class FakeSegmentItemFactory:
    def __init__(self, connection):
        self._connection = connection

    def create(self, startNode, endNode):
        return FakeSegmentItem(startNode, endNode, self._connection)


class TestCleanConnector:
    def testDPconnectionUsingBothTwoConnector(self):
        # requirements
        rad = 4
        dpConnection = _fc.createFullDoublePipeConnectionMock("dpConnectionName")

        segmentItemFactory = FakeSegmentItemFactory(dpConnection)

        # usage
        with _m.patch(
            "trnsysGUI.connection.getNiceConnector.NiceConnectorBothTwo._addGraphicsItems", return_value=None
        ) as mockMethod:
            connector = _gnc.NiceConnectorBothTwo(dpConnection, segmentItemFactory, rad)
            connector.createNiceConn()

        # test
        assert dpConnection.fromPort.createdAtSide == 2
        assert dpConnection.toPort.createdAtSide == 2
        assert mockMethod.call_count == 1
        newGraphicalItems = mockMethod.call_args[0][0]
        assert len(newGraphicalItems) == 9
        for i, item in enumerate(newGraphicalItems):
            if i < 5:
                assert isinstance(item, FakeSegmentItem)
            else:
                assert isinstance(item, _ci.CornerItem)


# things to test
# connection.fromPort.createdAtSide
# connection.toPort.createdAtSide
# logger?
# connection.firstS

# In need of patching
# connection.logger.debug(self.logStatement)
# connection.clearConn()
# connection.parent.diagramScene.addItem(gItem) or use _addGraphicsItems as a spy?
# connection.fromPort.scenePos()
# connection.toPort.scenePos()
# connection.printConnNodes() ?

# possible issues:
# DoublePipeSegmentItem needs to be instantiated.
