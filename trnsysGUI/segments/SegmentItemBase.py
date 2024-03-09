# pylint: skip-file
# type: ignore
from __future__ import annotations

import math as _math
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.CornerItem as _ci
import trnsysGUI.HorizSegmentMoveCommand as _smvc
from trnsysGUI.connection import delete as _cdel

# This is needed to avoid a circular import but still be able to type check
if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.connectionBase as _cib


def calcDist(p1, p2):
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class SegmentItemBase(_qtw.QGraphicsItemGroup):
    def __init__(self, startNode, endNode, parent: _cib.ConnectionBase):
        """
        A connection is displayed as a chain of segmentItems (stored in Connection.segments)
        Parameters.
        ----------
        startNode
        endNode
        parent: type(parent): Connection
        """

        super().__init__(parent=parent)
        self.logger = parent.logger

        self.setFlag(self.ItemIsSelectable, True)

        self.dragged = False
        self.initialised = False
        self.connection = parent

        self.firstChild = None
        self.secondChild = None
        self.cornerChild = None

        self.linePoints = None

        self.startNode = startNode
        self.endNode = endNode

        # These nodes are the nodes before and after the crossing
        self.start = None
        self.end = None

        self.firstLine = None
        self.secondLine = None
        self.secondCorner = None
        self.thirdCorner = None

        # Used to only create the child objects once
        self._startingXWhileDragging: _tp.Optional[float] = None

        self._insertIntoParentSegments()

        self.setToolTip(self.connection.displayName)

    def segLength(self):
        return calcDist(self.line().p1(), self.line().p2())

    def line(self):
        return self.linePoints

    def setLine(self, *args):
        self.setZValue(-1)
        if len(args) == 2:
            p1, p2 = args
            x1 = p1.x()
            y1 = p1.y()
            x2 = p2.x()
            y2 = p2.y()
        else:
            x1, y1, x2, y2 = args

        self._setLineImpl(x1, y1, x2, y2)

    def _setLineImpl(self, x1, y1, x2, y2):
        raise NotImplementedError()

    def _insertIntoParentSegments(self):
        """
        This function inserts the segment in correct order to the segment list of the connection.
        Returns
        -------

        """
        previousSegment = None

        for segment in self.connection.segments:
            if segment.endNode is self.startNode:
                previousSegment = segment

        if hasattr(self.startNode.parent, "fromPort"):
            self.connection.segments.insert(0, self)
            return

        self.connection.segments.insert(self.connection.segments.index(previousSegment) + 1, self)

    def isIntermediateSegment(self) -> bool:
        return isinstance(self.startNode.parent, _ci.CornerItem) and isinstance(self.endNode.parent, _ci.CornerItem)

    def isFirstOrLastSegment(self) -> bool:
        isFirstSegment = self.isFirstSegment()
        isLastSegment = self._isLastSegment()
        isFirstOrLastSegment = isFirstSegment or isLastSegment
        return isFirstOrLastSegment

    def isFirstSegment(self) -> bool:
        isFirstSegment = hasattr(self.startNode.parent, "fromPort") and not self.startNode.prevN()
        return isFirstSegment

    def _isLastSegment(self) -> bool:
        isLastSegment = hasattr(self.endNode.parent, "fromPort") and not self.endNode.nextN()
        return isLastSegment

    def deleteNextHorizSeg(self, keepSeg, nextS):
        if not keepSeg:
            nodeTodelete1 = self.endNode
            nodeTodelete2 = self.endNode.nextN()
            self.endNode = nextS.endNode

            self.startNode.setNext(self.endNode)
            self.endNode.setPrev(self.startNode)

            # x-position of the ending point of the next segment line

            posx1 = self.connection.segments[self.connection.segments.index(self) + 2].line().p2().x()

            _cdel.deleteGraphicsItem(nextS)
            self.connection.segments.remove(nextS)
            _cdel.deleteGraphicsItem(nodeTodelete1.parent)

            indexOfSelf = self.connection.segments.index(self)
            nextVS = self.connection.segments[indexOfSelf + 1]

            _cdel.deleteGraphicsItem(nextVS)
            self.connection.segments.remove(nextVS)
            _cdel.deleteGraphicsItem(nodeTodelete2.parent)

            self.setLine(
                self.startNode.parent.scenePos().x(),
                self.startNode.parent.scenePos().y(),
                posx1,
                self.startNode.parent.scenePos().y(),
            )

    def deletePrevHorizSeg(self, keepPrevSeg, prevS):
        if not keepPrevSeg:
            nodeTodelete1 = self.startNode
            nodeTodelete2 = self.startNode.prevN()
            self.startNode = prevS.startNode

            self.startNode.setNext(self.endNode)
            self.endNode.setPrev(self.startNode)

            posx1 = self.connection.segments[self.connection.segments.index(self) - 2].line().p1().x()

            _cdel.deleteGraphicsItem(prevS)
            self.connection.segments.remove(prevS)
            _cdel.deleteGraphicsItem(nodeTodelete1.parent)

            indexOfSelf = self.connection.segments.index(self)
            nextVS = self.connection.segments[indexOfSelf - 1]

            _cdel.deleteGraphicsItem(nextVS)
            self.connection.segments.remove(nextVS)
            _cdel.deleteGraphicsItem(nodeTodelete2.parent)

            self.setLine(
                posx1,
                self.endNode.parent.scenePos().y(),
                self.endNode.parent.scenePos().x(),
                self.endNode.parent.scenePos().y(),
            )

    def _initDraggingFirstOrLastSegment(self) -> None:
        rad = self.connection.getRadius()

        if self.isFirstSegment():
            self.secondCorner = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self.connection)
            self.thirdCorner = _ci.CornerItem(
                -rad, -rad, 2 * rad, 2 * rad, self.secondCorner.node, self.endNode, self.connection
            )

            self.secondCorner.node.setNext(self.thirdCorner.node)
            self.startNode.setNext(self.secondCorner.node)
            self.endNode.setPrev(self.thirdCorner.node)

            self.endNode = self.secondCorner.node

            self.firstLine = self._createSegment(self.secondCorner.node, self.thirdCorner.node)
            self.secondLine = self._createSegment(self.thirdCorner.node, self.thirdCorner.node.nextN())

            self.secondCorner.setVisible(False)
            self.thirdCorner.setVisible(False)
            self.firstLine.setVisible(False)
            self.secondLine.setVisible(False)
        else:
            self.secondCorner = _ci.CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self.connection)
            self.thirdCorner = _ci.CornerItem(
                -rad, -rad, 2 * rad, 2 * rad, self.secondCorner.node, self.endNode, self.connection
            )

            self.secondCorner.node.setNext(self.thirdCorner.node)
            self.startNode.setNext(self.secondCorner.node)
            self.endNode.setPrev(self.thirdCorner.node)

            self.startNode = self.thirdCorner.node

            self.firstLine = self._createSegment(self.secondCorner.node.prevN(), self.secondCorner.node)
            self.secondLine = self._createSegment(self.secondCorner.node, self.thirdCorner.node)

            self.secondCorner.setVisible(False)
            self.thirdCorner.setVisible(False)
            self.firstLine.setVisible(False)
            self.secondLine.setVisible(False)

    def _createSegment(self, startNode, endNode) -> "SegmentItemBase":
        raise NotImplementedError()

    def isVertical(self):
        return self.line().p1().x() == self.line().p2().x()

    def isHorizontal(self):
        return self.line().p1().y() == self.line().p2().y()

    def _dragFirstOrLastSegment(self, newPos: _qtc.QPoint) -> None:
        if self.isFirstSegment():
            self.thirdCorner.setPos(newPos.x() - 10, newPos.y())

            self.secondCorner.setPos(newPos.x() - 10, self.connection.fromPort.scenePos().y())
            self.thirdCorner.node.nextN().parent.setY(newPos.y())

            self.firstLine.setLine(
                self.secondCorner.scenePos().x(),
                self.secondCorner.scenePos().y(),
                self.thirdCorner.scenePos().x(),
                newPos.y(),
            )
            self.secondLine.setLine(
                self.thirdCorner.scenePos().x(),
                self.thirdCorner.scenePos().y(),
                self.thirdCorner.node.nextN().parent.scenePos().x(),
                self.thirdCorner.node.nextN().parent.scenePos().y(),
            )
            self.setLine(
                self.startNode.parent.fromPort.scenePos().x(),
                self.startNode.parent.fromPort.scenePos().y(),
                self.secondCorner.scenePos().x(),
                self.secondCorner.scenePos().y(),
            )

            self.secondCorner.setZValue(100)
            self.thirdCorner.setZValue(100)
            self.firstLine.setZValue(1)
            self.secondLine.setZValue(1)

            self.secondCorner.setVisible(True)
            self.thirdCorner.setVisible(True)
            self.firstLine.setVisible(True)
            self.secondLine.setVisible(True)

        else:
            self.secondCorner.setPos(newPos.x() + 10, newPos.y())

            self.thirdCorner.setPos(newPos.x() + 10, self.connection.toPort.scenePos().y())
            self.secondCorner.node.prevN().parent.setY(newPos.y())

            self.firstLine.setLine(
                self.secondCorner.node.prevN().parent.scenePos().x(),
                newPos.y(),
                self.secondCorner.scenePos().x(),
                newPos.y(),
            )
            self.secondLine.setLine(
                self.secondCorner.scenePos().x(),
                self.secondCorner.scenePos().y(),
                self.thirdCorner.scenePos().x(),
                self.thirdCorner.scenePos().y(),
            )
            self.setLine(
                self.thirdCorner.scenePos().x(),
                self.thirdCorner.scenePos().y(),
                self.endNode.parent.toPort.scenePos().x(),
                self.endNode.parent.toPort.scenePos().y(),
            )

            self.secondCorner.setZValue(100)
            self.thirdCorner.setZValue(100)
            self.firstLine.setZValue(1)
            self.secondLine.setZValue(1)

            self.secondCorner.setVisible(True)
            self.thirdCorner.setVisible(True)
            self.firstLine.setVisible(True)
            self.secondLine.setVisible(True)

    def renameConn(self):
        self.connection.parent.showSegmentDlg(self)

    def contextMenuEvent(self, event):
        menu = self._getContextMenu()

        menu.exec(event.screenPos())

    def _getContextMenu(self) -> _qtw.QMenu:
        menu = _qtw.QMenu()
        a1 = menu.addAction("Rename...")
        a1.triggered.connect(self.renameConn)
        a2 = menu.addAction("Delete this connection")
        a2.triggered.connect(self.connection.createDeleteUndoCommandAndAddToStack)
        a3 = menu.addAction("Invert this connection")
        a3.triggered.connect(self.connection.invertConnection)
        a4 = menu.addAction("Toggle name")
        a4.triggered.connect(self.connection.toggleLabelVisible)
        a5 = menu.addAction("Toggle mass flow")
        a5.triggered.connect(self.connection.toggleMassFlowLabelVisible)
        return menu

    def setColorAndWidthAccordingToMassflow(self, color, width):
        raise NotImplementedError()

    def resetLinePens(self) -> None:
        if self.connection.isConnectionSelected:
            self._setSelectedLinesPen()
        else:
            self._setStandardLinesPens()

    def _setStandardLinesPens(self):
        raise NotImplementedError()

    def _setSelectedLinesPen(self):
        raise NotImplementedError()

    def _createSelectedLinesPen(self) -> _qtg.QPen:
        color = _qtg.QColor(125, 242, 189)
        width = 4

        selectPen = _qtg.QPen(color, width)

        if not self.connection.shallBeSimulated:
            selectPen.setStyle(_qtc.Qt.DashLine)

        return selectPen

    @_tp.override
    def mousePressEvent(self, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        self.connection.onMousePressed(self, event)

    @_tp.override
    def mouseMoveEvent(self, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        self.connection.onMouseMoved(event)

    @_tp.override
    def mouseReleaseEvent(self, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        self.connection.onMouseReleased(event)
