from __future__ import annotations

import dataclasses as _dc
import typing as _tp
from PyQt5 import QtCore as _qtc

from trnsysGUI import CornerItem as _ci

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.connectionBase as _cb
    import trnsysGUI.segments.segmentItemFactoryBase as _sifb


@_dc.dataclass
class NiceConnectorBase:
    # pylint: disable = too-many-instance-attributes
    connection: _cb.ConnectionBase
    segmentItemFactory: _sifb.SegmentItemFactoryBase
    rad: float
    nrOfCorners: _tp.Optional[int] = None
    fromSide: _tp.Optional[int] = None
    toSide: _tp.Optional[int] = None
    logStatement: _tp.Optional[str] = None
    operation: _tp.Optional[str] = None
    printConnNodes: bool = False
    setFirstSeg: bool = False
    createBothPorts: bool = True

    def createNiceConn(self):
        self._resetConnectionWithValues()

        corners = self._getConnectionCorners(self.nrOfCorners)
        corners = self._setNextConnectionCorner(corners)

        segs = self._connectWithSegments(corners)

        self._connectStartAndEndNodes(corners[0], corners[-1])

        self._addGraphicsItems(segs + corners)

        points = self._getPoints(self.operation)

        self._setSegLines(segs, points)
        if self.printConnNodes:
            self.connection.printConnNodes()

        self._setCornerFlags(corners)

        self._setCornerZvalues(corners, 100)
        if self.nrOfCorners in (1, 2):
            self._setCornerZvalues([self.connection.toPort, self.connection.fromPort], 100)

        self.connection.logger.debug("Here in niceconn")
        self._setCornerPositions(corners, points)

        if self.setFirstSeg:
            self.connection.firstS = segs[0]
            self.connection.logger.debug("Conn has now " + str(self.connection.firstS))

    def _resetConnectionWithValues(self):
        self.connection.fromPort.createdAtSide = self.fromSide
        if self.createBothPorts:
            self.connection.toPort.createdAtSide = self.toSide
        self.connection.logger.debug(self.logStatement)
        self.connection.clearConn()

    def _getConnectionCorners(self, nrOfCorners):
        rad = self.rad
        endNode, startNode = self._getStartAndEndNode()

        cornerCur = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, startNode, None, self.connection)
        corners = [cornerCur]
        for _ in range(nrOfCorners - 2):
            corner = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, cornerCur.node, None, self.connection)
            corners.append(corner)
            cornerCur = corner

        corners.append(_ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, cornerCur.node, endNode, self.connection))
        return corners

    def _getStartAndEndNode(self):
        startNode = self.connection.startNode
        endNode = self.connection.endNode
        return endNode, startNode

    @staticmethod
    def _setNextConnectionCorner(corners):
        for i in range(len(corners) - 1):
            corners[i].node.setNext(corners[i + 1].node)
        return corners

    def _connectWithSegments(self, corners):
        endNode, startNode = self._getStartAndEndNode()

        segs = [self.segmentItemFactory.create(startNode, corners[0].node)]
        for i in range(len(corners) - 1):
            segs.append(self.segmentItemFactory.create(corners[i].node, corners[i + 1].node))

        segs.append(self.segmentItemFactory.create(corners[-1].node, endNode))
        return segs

    def _connectStartAndEndNodes(self, toStart, toEnd):
        endNode, startNode = self._getStartAndEndNode()
        startNode.setNext(toStart.node)
        endNode.setPrev(toEnd.node)

    def _addGraphicsItems(self, gItems):
        for gItem in gItems:
            self.connection.parent.diagramScene.addItem(gItem)

    def _getPoints(self, operation):
        posEnd, posStart = self._getStartAndEndPositions()
        points = [posStart]

        baseLineHeight = max(posStart.y(), posEnd.y()) + 100.6
        portOffset = 30

        if operation == "add":
            point1 = _qtc.QPointF(posStart.x() + portOffset, posStart.y())
        elif operation == "subtract":
            point1 = _qtc.QPointF(posStart.x() - portOffset, posStart.y())
        else:
            raise NotImplementedError()

        points.append(point1)
        points.append(_qtc.QPointF(point1.x(), baseLineHeight))

        if operation == "add":
            point3 = _qtc.QPointF(posEnd.x() + portOffset, baseLineHeight)
        elif operation == "subtract":
            point3 = _qtc.QPointF(posEnd.x() - portOffset, baseLineHeight)
        else:
            raise NotImplementedError()

        points.append(point3)
        points.append(_qtc.QPointF(point3.x(), posEnd.y()))
        points.append(posEnd)

        return points

    def _getStartAndEndPositions(self):
        posStart = self.connection.fromPort.scenePos()
        posEnd = self.connection.toPort.scenePos()
        return posEnd, posStart

    @staticmethod
    def _setSegLines(segs, points):
        assert len(segs) + 1 == len(points)

        for i, seg in enumerate(segs):
            seg.setLine(points[i], points[i + 1])

    @staticmethod
    def _setCornerFlags(corners):
        for corner in corners:
            corner.setFlag(corner.ItemSendsScenePositionChanges, True)

    @staticmethod
    def _setCornerZvalues(corners, value):
        for corner in corners:
            corner.setZValue(value)

    @staticmethod
    def _setCornerPositions(corners, points):
        assert len(corners) + 2 == len(points)
        for i, corner in enumerate(corners):
            corner.setPos(points[i + 1])


class NiceConnectorBothTwo(NiceConnectorBase):
    def __init__(self, connection, segmentItemFactory, rad):
        super().__init__(connection, segmentItemFactory, rad)
        self.nrOfCorners = 4
        self.fromSide = 2
        self.toSide = 2
        self.logStatement = "NiceConn 2 to 2"
        self.operation = "add"


class NiceConnectorBothZero(NiceConnectorBase):
    def __init__(self, connection, segmentItemFactory, rad):
        super().__init__(connection, segmentItemFactory, rad)
        self.nrOfCorners = 4
        self.fromSide = 0
        self.toSide = 0
        self.logStatement = "NiceConn 0 to 0"
        self.operation = "subtract"


class NiceConnectorOther(NiceConnectorBase):
    def __init__(self, connection, segmentItemFactory, rad):
        super().__init__(connection, segmentItemFactory, rad)
        self.nrOfCorners = 2
        self.fromSide = self.connection.fromPort.side
        self.toSide = self.connection.toPort.side
        self.logStatement = "Ports are directed to each other"
        self.printConnNodes = True
        self.setFirstSeg = True

    def _getPoints(self, operation):
        posEnd, posStart = self._getStartAndEndPositions()

        points = [posStart]

        midx = self._getMiddleCoordinate(posStart, posEnd)

        points.append(_qtc.QPointF(midx, posStart.y()))
        points.append(_qtc.QPointF(midx, posEnd.y()))
        points.append(posEnd)

        return points

    @staticmethod
    def _getMiddleCoordinate(pos1, pos2):
        midx = pos1.x() + 0.5 * (pos2.x() - pos1.x())
        return midx


class NiceConnectorFromAbove(NiceConnectorBase):
    def __init__(self, connection, segmentItemFactory, rad, fromSide=1, logStatement="To port ABOVE from port 1"):
        super().__init__(connection, segmentItemFactory, rad)
        self.nrOfCorners = 1
        self.fromSide = fromSide
        self.logStatement = logStatement
        self.createBothPorts = False
        self.setFirstSeg = True
        if fromSide == 1:
            self.operation = "subtract"
        elif fromSide == 3:
            self.operation = "add"

    def _getConnectionCorners(self, nrOfCorners):
        rad = self.rad
        endNode, startNode = self._getStartAndEndNode()
        corners = [_ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, startNode, endNode, self.connection)]

        return corners

    def _getPoints(self, operation):
        posEnd, posStart = self._getStartAndEndPositions()

        points = [posStart]

        if operation == "add":
            points.append(_qtc.QPointF(posStart.x(), posEnd.y() + 0.333))
        elif operation == "subtract":
            points.append(_qtc.QPointF(posStart.x(), posEnd.y() - 0.333))

        points.append(posEnd)

        return points


class NiceConnectorFromBelow(NiceConnectorBase):
    def __init__(
        self,
        connection,
        segmentItemFactory,
        rad,
        fromSide=1,
        logStatement="To port BELOW from port 1",
        operation="subtract",
    ):
        super().__init__(connection, segmentItemFactory, rad)
        self.nrOfCorners = 2
        self.fromSide = fromSide
        self.logStatement = logStatement
        self.createBothPorts = False
        self.setFirstSeg = True
        self.printConnNodes = True
        self.operation = operation

    def _getPoints(self, operation):
        posEnd, posStart = self._getStartAndEndPositions()

        points = [posStart]
        if operation == "add":
            offsetPoint = posStart.y() + 15.666
        elif operation == "subtract":
            offsetPoint = posStart.y() - 15.666
        else:
            raise NotImplementedError()

        points.append(_qtc.QPointF(posStart.x(), offsetPoint))
        points.append(_qtc.QPointF(posEnd.x(), offsetPoint))

        points.append(posEnd)

        return points
