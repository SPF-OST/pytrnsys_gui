from __future__ import annotations

import dataclasses as _dc
import typing as _tp
from PyQt5 import QtCore as _qtc

from trnsysGUI import cornerItem as _ci

if _tp.TYPE_CHECKING:
    import PyQt5.QtWidgets as _qtw

    from trnsysGUI import PortItemBase as _pib
    import trnsysGUI.connection.connectionBase as _cb
    import trnsysGUI.segments.segmentItemFactoryBase as _sifb
    import trnsysGUI.segments.node as _node
    import trnsysGUI.segments.segmentItemBase as _sib


@_dc.dataclass
class NiceConnectorBase:
    # pylint: disable = too-many-instance-attributes
    connection: _cb.ConnectionBase
    segmentItemFactory: _sifb.SegmentItemFactoryBase
    rad: int

    nrOfCorners: int = _dc.field(init=False)

    def __post_init__(self):
        self.fromSide: _tp.Optional[int] = None
        self.toSide: _tp.Optional[int] = None
        self.logStatement: _tp.Optional[str] = None
        self.operation: str = ""
        self.printConnNodes: bool = False
        self.setFirstSeg: bool = False
        self.createBothPorts: bool = True

    def createNiceConn(self) -> None:
        self._resetConnectionWithValues()

        corners = self._getConnectionCorners(self.nrOfCorners)
        corners = self._setNextConnectionCorner(corners)

        segs = self._connectWithSegments(corners)

        self._connectStartAndEndNodes(corners[0], corners[-1])

        graphicItems = [*segs, *corners]
        self._addGraphicsItems(graphicItems)

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

    def _resetConnectionWithValues(self) -> None:
        self.connection.fromPort.createdAtSide = self.fromSide
        if self.createBothPorts:
            self.connection.toPort.createdAtSide = self.toSide
        self.connection.logger.debug(self.logStatement)
        self.connection.clearConn()

    def _getConnectionCorners(self, nrOfCorners: int) -> list[_ci.CornerItem]:
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

    def _getStartAndEndNode(self) -> _tp.Tuple[_node.Node, _node.Node]:
        startNode = self.connection.startNode
        endNode = self.connection.endNode
        return endNode, startNode

    @staticmethod
    def _setNextConnectionCorner(corners: list[_ci.CornerItem]) -> list[_ci.CornerItem]:
        for i in range(len(corners) - 1):
            corners[i].node.setNext(corners[i + 1].node)
        return corners

    def _connectWithSegments(self, corners: _tp.Sequence[_ci.CornerItem]) -> list[_sib.SegmentItemBase]:
        endNode, startNode = self._getStartAndEndNode()

        segs = [self.segmentItemFactory.create(startNode, corners[0].node)]
        for i in range(len(corners) - 1):
            segs.append(self.segmentItemFactory.create(corners[i].node, corners[i + 1].node))

        segs.append(self.segmentItemFactory.create(corners[-1].node, endNode))
        return segs

    def _connectStartAndEndNodes(self, toStart: _ci.CornerItem, toEnd: _ci.CornerItem) -> None:
        endNode, startNode = self._getStartAndEndNode()
        startNode.setNext(toStart.node)
        endNode.setPrev(toEnd.node)

    def _addGraphicsItems(self, gItems: _tp.Sequence[_qtw.QGraphicsItem]) -> None:
        for gItem in gItems:
            self.connection.parent.diagramScene.addItem(gItem)

    def _getPoints(self, operation: str) -> list[_qtc.QPointF]:
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

    def _getStartAndEndPositions(self) -> _tp.Tuple[_qtc.QPointF, _qtc.QPointF]:
        posStart = self.connection.fromPort.scenePos()
        posEnd = self.connection.toPort.scenePos()
        return posEnd, posStart

    @staticmethod
    def _setSegLines(segs: _tp.Sequence[_sib.SegmentItemBase], points: _tp.Sequence[_qtc.QPointF]) -> None:
        assert len(segs) + 1 == len(points)

        for i, seg in enumerate(segs):
            seg.setLine(points[i], points[i + 1])

    @staticmethod
    def _setCornerFlags(corners: _tp.Sequence[_ci.CornerItem]):
        for corner in corners:
            corner.setFlag(corner.ItemSendsScenePositionChanges, True)

    @staticmethod
    def _setCornerZvalues(corners: _tp.Sequence[_tp.Union[_pib.PortItemBase, _ci.CornerItem]], value: float):
        for corner in corners:
            corner.setZValue(value)

    @staticmethod
    def _setCornerPositions(corners: _tp.Sequence[_ci.CornerItem], points):
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


@_dc.dataclass
class NiceConnectorFromAbove(NiceConnectorBase):
    fromSide: int = 1
    logStatement: str = "To port ABOVE from port 1"

    def __post_init__(self) -> None:
        self.nrOfCorners = 1
        self.createBothPorts = False
        self.setFirstSeg = True
        self.printConnNodes: bool = False

        if self.fromSide == 1:
            self.operation = "subtract"
        elif self.fromSide == 3:
            self.operation = "add"

    def _getConnectionCorners(self, nrOfCorners: int) -> list[_ci.CornerItem]:
        rad = self.rad
        endNode, startNode = self._getStartAndEndNode()
        corners = [_ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, startNode, endNode, self.connection)]

        return corners

    def _getPoints(self, operation: str) -> list[_qtc.QPointF]:
        posEnd, posStart = self._getStartAndEndPositions()

        points = [posStart]

        if operation == "add":
            points.append(_qtc.QPointF(posStart.x(), posEnd.y() + 0.333))
        elif operation == "subtract":
            points.append(_qtc.QPointF(posStart.x(), posEnd.y() - 0.333))

        points.append(posEnd)

        return points


@_dc.dataclass
class NiceConnectorFromBelow(NiceConnectorBase):
    fromSide: int = 1
    logStatement: str = "To port BELOW from port 1"
    operation: str = "subtract"

    def __post_init__(self) -> None:
        self.nrOfCorners = 2
        self.createBothPorts = False
        self.setFirstSeg = True
        self.printConnNodes = True

    def _getPoints(self, operation: str) -> list[_qtc.QPointF]:
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
