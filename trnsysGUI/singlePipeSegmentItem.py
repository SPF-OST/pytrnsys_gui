import typing as tp

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QLinearGradient, QBrush, QPen
from PyQt5.QtWidgets import QGraphicsLineItem

from trnsysGUI.CornerItem import CornerItem  # type: ignore[attr-defined]
from trnsysGUI.SegmentItemBase import SegmentItemBase  # type: ignore[attr-defined]

# This is needed to avoid a circular import but still be able to type check
if tp.TYPE_CHECKING:
    from trnsysGUI.Connection import Connection  # type: ignore[attr-defined]  # pylint: disable=unused-import


class SinglePipeSegmentItem(SegmentItemBase):
    def __init__(self, startNode, endNode, parent: "Connection"):
        super().__init__(startNode, endNode, parent)

        self.singleLine = QGraphicsLineItem(self)
        self.linearGrad = None
        self.initGrad()

    def _createSegment(self, startNode, endNode) -> "SegmentItemBase":
        return SinglePipeSegmentItem(startNode, endNode, self.connection)

    def _setLineImpl(self, x1, y1, x2, y2):
        self.initGrad()
        self.singleLine.setLine(x1, y1, x2, y2)
        self.linePoints = self.singleLine.line()

    def initGrad(self):
        color = QtCore.Qt.white

        pen1 = QtGui.QPen(color, 4)

        if isinstance(self.startNode.parent, CornerItem):
            startBlock = self.startNode.firstNode().parent
        else:
            startBlock = self.startNode.parent

        if isinstance(self.endNode.parent, CornerItem):
            endBlock = self.endNode.lastNode().parent
        else:
            endBlock = self.endNode.parent

        self.linearGrad = QLinearGradient(
            QPointF(startBlock.fromPort.scenePos().x(), startBlock.fromPort.scenePos().y()),
            QPointF(endBlock.toPort.scenePos().x(), endBlock.toPort.scenePos().y()),
        )
        self.linearGrad.setColorAt(0, QtCore.Qt.blue)
        self.linearGrad.setColorAt(1, QtCore.Qt.red)

        self.linearGrad.setColorAt(0, QtCore.Qt.gray)
        self.linearGrad.setColorAt(1, QtCore.Qt.black)

        pen1.setBrush(QBrush(self.linearGrad))

        self.singleLine.setPen(pen1)

    def updateGrad(self):
        color = QtCore.Qt.white
        pen1 = QtGui.QPen(color, 4)

        totLenConn = self.connection.totalLength()
        partLen1 = self.connection.partialLength(self.startNode)
        partLen2 = self.connection.partialLength(self.endNode)

        if isinstance(self.startNode.parent, CornerItem):
            startGradP = QPointF(self.startNode.parent.scenePos().x(), self.startNode.parent.scenePos().y())
        elif self.startNode.prevN() is None:
            startGradP = QPointF(
                self.startNode.parent.fromPort.scenePos().x(), self.startNode.parent.fromPort.scenePos().y()
            )
        else:
            startGradP = QPointF(self.line().p1().x(), self.line().p1().y())

        if isinstance(self.endNode.parent, CornerItem):
            endGradP = QPointF(self.endNode.parent.scenePos().x(), self.endNode.parent.scenePos().y())
        elif self.endNode.nextN() is None:
            endGradP = QPointF(self.endNode.parent.toPort.scenePos().x(), self.endNode.parent.toPort.scenePos().y())
        else:
            endGradP = QPointF(self.line().p2().x(), self.line().p2().y())

        self.linearGrad = QLinearGradient(startGradP, endGradP)

        self.linearGrad.setColorAt(0, self.interpolate(partLen1, totLenConn))
        self.linearGrad.setColorAt(1, self.interpolate(partLen2, totLenConn))

        pen1.setBrush(QBrush(self.linearGrad))

        self.singleLine.setPen(pen1)

    def setSelect(self, isSelected: bool) -> None:
        if isSelected:
            selectPen = self._createSelectPen()
            self.singleLine.setPen(selectPen)
        else:
            self.updateGrad()

    def setColorAndWidthAccordingToMassflow(self, color, width):
        pen1 = QPen(color, width)
        self.singleLine.setPen(pen1)
