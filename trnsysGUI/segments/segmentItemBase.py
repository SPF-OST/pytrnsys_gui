from __future__ import annotations

import math as _math
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.cornerItem as _ci
import trnsysGUI.segments.node as _node

# This is needed to avoid a circular import but still be able to type check
if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.connectionBase as _cib


def calcDist(p1, p2):
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class SegmentItemBase(_qtw.QGraphicsItemGroup):
    def __init__(
        self,
        startNode: _node.Node,
        endNode: _node.Node,
        parent: _cib.ConnectionBase,
    ) -> None:
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

        self.connection = parent

        self.linePoints = _qtc.QLineF()

        self.startNode = startNode
        self.endNode = endNode

        self._insertIntoParentSegments()

        self.setToolTip(self.connection.displayName)

    def setEndNode(self, newEndNode) -> None:
        self.endNode = newEndNode
        self.endNode.setPrev(self.startNode)
        self.startNode.setNext(self.endNode)

    def line(self) -> _qtc.QLineF:
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

        self.connection.segments.insert(
            self.connection.segments.index(previousSegment) + 1, self
        )

    def isIntermediateSegment(self) -> bool:
        return isinstance(
            self.startNode.parent, _ci.CornerItem
        ) and isinstance(self.endNode.parent, _ci.CornerItem)

    def isFirstOrLastSegment(self) -> bool:
        isFirstSegment = self.isFirstSegment()
        isLastSegment = self.isLastSegment()
        isFirstOrLastSegment = isFirstSegment or isLastSegment
        return isFirstOrLastSegment

    def isFirstSegment(self) -> bool:
        isFirstSegment = (
            hasattr(self.startNode.parent, "fromPort")
            and not self.startNode.prevN()
        )
        return isFirstSegment

    def isLastSegment(self) -> bool:
        isLastSegment = (
            hasattr(self.endNode.parent, "fromPort")
            and not self.endNode.nextN()
        )
        return isLastSegment

    def isVertical(self) -> bool:
        return self.line().p1().x() == self.line().p2().x()

    def isHorizontal(self) -> bool:
        return self.line().p1().y() == self.line().p2().y()

    def isZeroLength(self) -> bool:
        return self.line().isNull()

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
        a2.triggered.connect(
            self.connection.createDeleteUndoCommandAndAddToStack
        )
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
