import unittest.mock as _m

import trnsysGUI.segments.doublePipeSegmentItemFactory as _dpsif
import trnsysGUI.connection.getNiceConnector as _gnc
from trnsysGUI import CornerItem as _ci

from . import fakeConnections as _fc

from .. import testStorageTank as _tst

# CreateConnectionMock in testDoubleDoublePipeConnector for double pipe connection
# CreateConnectionMock in testStorageTank for single pipe connection
# spConnection = _tst.TestStorageTank._createConnectionMock("spConnectionName")


class FakeSegmentItem(_fc.StrictMockBase):
    def __init__(self, startNode, endNode, connection, **kwargs):
        super().__init__(**kwargs)
        self.startNode = startNode
        self.endNode = endNode
        self.connection = connection

    def setLine(self, point1, point2):
        pass


class TestCleanConnector:
    def testDPconnectionUsingBothTwoConnector(self):
        # requirements
        rad = 4
        dpConnection = _fc.createFullDoublePipeConnectionMock("dpConnectionName")

        # monkeypatch the factory
        def create(self, startNode, endNode):
            return FakeSegmentItem(startNode, endNode, self._connection)

        _dpsif.DoublePipeSegmentItemFactory.create = create

        segmentItemFactory = _dpsif.DoublePipeSegmentItemFactory(dpConnection)

        # usage
        with _m.patch(
            "trnsysGUI.connection.getNiceConnector.NiceConnectorBothTwo._addGraphicsItems", return_value=None
        ) as mock_method:
            connector = _gnc.NiceConnectorBothTwo(dpConnection, segmentItemFactory, rad)
            connector.createNiceConn()

        # test
        assert dpConnection.fromPort.createdAtSide == 2
        assert dpConnection.toPort.createdAtSide == 2
        assert mock_method.call_count == 1
        newGraphicalItems = mock_method.call_args[0][0]
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
