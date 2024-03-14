from __future__ import annotations

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.segments.Node as _node

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.connectionBase as _cb


class CornerItem(_qtw.QGraphicsEllipseItem):
    def __init__(
        self,
        x: float,
        y: float,
        r1: float,
        r2: float,
        prevNode: _node.Node,
        nextNode: _node.Node,
        connection: _cb.ConnectionBase,
    ) -> None:
        super().__init__(x, y, r1, r2, parent=connection)

        self.logger = connection.logger

        self._connection = connection
        self.setBrush(_qtg.QBrush(_qtc.Qt.black))
        self.node = _node.Node(self, prevNode, nextNode)

    def itemChange(self, change, value):
        if change != self.ItemScenePositionHasChanged:
            return super().itemChange(change, value)

        segmentBefore, segmentAfter = self._connection.getPreviousAndNextSegment(self.node)

        beforeFromPos, afterToPos = self._getBeforeFromPosAndAfterToPos()

        segmentBefore.setLine(beforeFromPos, self.scenePos())
        segmentAfter.setLine(self.scenePos(), afterToPos)

        for segment in self._connection.segments:
            segment.resetLinePens()

        return value

    def _getBeforeFromPosAndAfterToPos(self) -> _tp.Tuple[_qtc.QPointF, _qtc.QPointF]:
        fromPort = self._connection.fromPort
        toPort = self._connection.toPort

        segmentBefore, segmentAfter = self._connection.getPreviousAndNextSegment(self.node)

        previousNode = self.node.prevN()
        nextNode = self.node.nextN()

        beforeFromPos = fromPort.scenePos() if segmentBefore.isFirstSegment() else previousNode.parent.scenePos()
        afterToPos = toPort.scenePos() if segmentAfter.isLastSegment() else nextNode.parent.scenePos()

        return beforeFromPos, afterToPos
