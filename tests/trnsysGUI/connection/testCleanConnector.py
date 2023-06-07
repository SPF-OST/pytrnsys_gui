import unittest.mock as _m

import trnsysGUI.connection.getNiceConnector as _gnc
from trnsysGUI import cornerItem as _ci

from . import fakeConnections as _fc

spConnection = _fc.createSimpleSPConnectionMock("spConnectionName")


class FakeSegmentItem(_fc.StrictMockBase):
    def __init__(self, startNode, endNode, connection, **kwargs):
        super().__init__(**kwargs)
        self.startNode = startNode
        self.endNode = endNode
        self.connection = connection
        self.lineStart = None
        self.lineEnd = None

    def setLine(self, point1, point2):
        self.lineStart = point1
        self.lineEnd = point2


class FakeSegmentItemFactory:
    def __init__(self, connection):
        self._connection = connection

    def create(self, startNode, endNode):
        return FakeSegmentItem(startNode, endNode, self._connection)


class TestCleanConnector:
    def testDPconnectionUsingBothTwoConnector(self):
        self._runNiceConnWithTests(
            connectorType=_gnc.NiceConnectorBothTwo,
            patchString="NiceConnectorBothTwo",
            addItemCount=1,
            fromPortSide=2,
            toPortSide=2,
            nrOfNewItems=9,
            nSegsExpected=5,
            xStartCoordsExpected=[0.0, 30.0, 30.0, 130.0, 130.0],
            xEndCoordsExpected=[30.0, 30.0, 130.0, 130.0, 100.0],
            yStartCoordsExpected=[0.0, 0.0, 200.6, 200.6, 100.0],
            yEndCoordsExpected=[0.0, 200.6, 200.6, 100.0, 100.0],
        )

    def testDPconnectionUsingBothZeroConnector(self):
        self._runNiceConnWithTests(
            patchString="NiceConnectorBothZero",
            connectorType=_gnc.NiceConnectorBothZero,
            addItemCount=1,
            fromPortSide=0,
            toPortSide=0,
            nrOfNewItems=9,
            nSegsExpected=5,
            xStartCoordsExpected=[0.0, -30.0, -30.0, 70.0, 70.0],
            yStartCoordsExpected=[0.0, 0.0, 200.6, 200.6, 100.0],
            xEndCoordsExpected=[-30.0, -30.0, 70.0, 70.0, 100.0],
            yEndCoordsExpected=[0.0, 200.6, 200.6, 100.0, 100.0],
        )

    def testDPconnectionUsingOtherConnector(self):
        self._runNiceConnWithTests(
            connectorType=_gnc.NiceConnectorOther,
            patchString="NiceConnectorOther",
            addItemCount=1,
            fromPortSide=7,
            toPortSide=7,
            nrOfNewItems=5,
            nSegsExpected=3,
            xStartCoordsExpected=[0.0, 50.0, 50.0],
            xEndCoordsExpected=[50.0, 50.0, 100.0],
            yStartCoordsExpected=[0.0, 0.0, 100.0],
            yEndCoordsExpected=[0.0, 100.0, 100.0],
        )

    def testDPconnectionUsingFromAboveConnector(self):
        self._runNiceConnWithTests(
            connectorType=_gnc.NiceConnectorFromAbove,
            patchString="NiceConnectorFromAbove",
            addItemCount=1,
            fromPortSide=1,
            toPortSide=None,
            nrOfNewItems=3,
            nSegsExpected=2,
            xStartCoordsExpected=[0.0, 0.0],
            xEndCoordsExpected=[0.0, 100.0],
            yStartCoordsExpected=[0.0, 99.667],
            yEndCoordsExpected=[99.667, 100.0],
        )

    def testDPconnectionUsingFromAboveConnectorWithOtherPortSide(self):
        self._runNiceConnWithTests(
            connectorType=_gnc.NiceConnectorFromAbove,
            patchString="NiceConnectorFromAbove",
            addItemCount=1,
            fromPortSide=3,
            toPortSide=None,
            nrOfNewItems=3,
            nSegsExpected=2,
            xStartCoordsExpected=[0.0, 0.0],
            xEndCoordsExpected=[0.0, 100.0],
            yStartCoordsExpected=[0.0, 100.333],
            yEndCoordsExpected=[100.333, 100.0],
        )

    def testDPconnectionUsingFromBelowConnector(self):
        self._runNiceConnWithTests(
            connectorType=_gnc.NiceConnectorFromBelow,
            patchString="NiceConnectorFromBelow",
            addItemCount=1,
            fromPortSide=1,
            toPortSide=None,
            nrOfNewItems=5,
            nSegsExpected=3,
            xStartCoordsExpected=[0.0, 0.0, 100.0],
            xEndCoordsExpected=[0.0, 100.0, 100.0],
            yStartCoordsExpected=[0.0, -15.666, -15.666],
            yEndCoordsExpected=[-15.666, -15.666, 100.0],
        )

    def testDPconnectionUsingFromBelowConnectorWithOtherPortSide(self):
        self._runNiceConnWithTests(
            connectorType=_gnc.NiceConnectorFromBelow,
            patchString="NiceConnectorFromBelow",
            operation="add",
            addItemCount=1,
            fromPortSide=3,
            toPortSide=None,
            nrOfNewItems=5,
            nSegsExpected=3,
            xStartCoordsExpected=[0.0, 0.0, 100.0],
            xEndCoordsExpected=[0.0, 100.0, 100.0],
            yStartCoordsExpected=[0.0, 15.666, 15.666],
            yEndCoordsExpected=[15.666, 15.666, 100.0],
        )

    def _runNiceConnWithTests(  # pylint: disable = too-many-arguments, too-many-locals
        self,
        connectorType,
        addItemCount,
        fromPortSide,
        nSegsExpected,
        nrOfNewItems,
        patchString,
        toPortSide,
        xEndCoordsExpected,
        xStartCoordsExpected,
        yEndCoordsExpected,
        yStartCoordsExpected,
        operation="subtract",
    ):

        dpConnection, rad, segmentItemFactory = self._getSetup()
        mockMethod = self._runNiceConn(
            connectorType, dpConnection, patchString, rad, segmentItemFactory, fromPortSide, operation
        )

        assert dpConnection.fromPort.createdAtSide == fromPortSide
        if toPortSide:
            assert dpConnection.toPort.createdAtSide == toPortSide
        assert mockMethod.call_count == addItemCount
        newGraphicalItems = mockMethod.call_args[0][0]
        assert len(newGraphicalItems) == nrOfNewItems

        self._checkItemType(nSegsExpected, newGraphicalItems)

        xStartCoords, yStartCoords, xEndCoords, yEndCoords = self._getLineCoords(newGraphicalItems[0:nSegsExpected])

        assert xStartCoords == xStartCoordsExpected
        assert yStartCoords == yStartCoordsExpected
        assert xEndCoords == xEndCoordsExpected
        assert yEndCoords == yEndCoordsExpected

    @staticmethod
    def _getSetup():
        rad = 4
        dpConnection = _fc.createFullDoublePipeConnectionMock("dpConnectionName")
        segmentItemFactory = FakeSegmentItemFactory(dpConnection)
        return dpConnection, rad, segmentItemFactory

    @staticmethod
    def _runNiceConn(
        connectorType, dpConnection, patchString, rad, segmentItemFactory, fromPortSide=None, operation="subtract"
    ):
        fullPatchString = "trnsysGUI.connection.getNiceConnector." + patchString + "._addGraphicsItems"
        with _m.patch(fullPatchString, return_value=None) as mockMethod:
            if patchString == "NiceConnectorFromAbove":
                connectorType(dpConnection, segmentItemFactory, rad, fromSide=fromPortSide).createNiceConn()
            elif patchString == "NiceConnectorFromBelow":
                connectorType(
                    dpConnection, segmentItemFactory, rad, fromSide=fromPortSide, operation=operation
                ).createNiceConn()
            else:
                connectorType(dpConnection, segmentItemFactory, rad).createNiceConn()
        return mockMethod

    @staticmethod
    def _checkItemType(nSegsExpected, newGraphicalItems):
        for i, item in enumerate(newGraphicalItems):
            if i < nSegsExpected:
                assert isinstance(item, FakeSegmentItem)
            else:
                assert isinstance(item, _ci.CornerItem)

    @staticmethod
    def _getLineCoords(segments):
        xStartCoords = []
        yStartCoords = []
        xEndCoords = []
        yEndCoords = []

        for seg in segments:
            xStartCoords.append(seg.lineStart.x())
            yStartCoords.append(seg.lineStart.y())
            xEndCoords.append(seg.lineEnd.x())
            yEndCoords.append(seg.lineEnd.y())

        return xStartCoords, yStartCoords, xEndCoords, yEndCoords
