# pylint: skip-file
# type: ignore

from math import sqrt
import typing as tp

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QLinearGradient, QBrush
from PyQt5.QtWidgets import QGraphicsLineItem

from trnsysGUI.CornerItem import CornerItem
from trnsysGUI.SegmentItemBase import SegmentItemBase

# This is needed to avoid a circular import but still be able to type check
if tp.TYPE_CHECKING:
    from trnsysGUI.Connection import Connection


class SinglePipeSegmentItem(SegmentItemBase):
    def __init__(self, startNode, endNode, parent: "Connection"):
        super().__init__(startNode, endNode, parent)

        self.singleLine = QGraphicsLineItem(self)
        self.linearGrad = None
        self.initGrad()

    def _createSegment(self, startNode, endNode) -> "SegmentItemBase":
        return SinglePipeSegmentItem(startNode, endNode, self.parent)

    def _setLineImpl(self, x1, y1, x2, y2):
        self.initGrad()
        self.singleLine.setLine(x1, y1, x2, y2)
        self.linePoints = self.singleLine.line()

    def initGrad(self):
        """
        Initialize gradient
        Returns
        -------

        """
        # color = QColor(177, 202, 211)
        # color = QColor(3, 124, 193)
        color = QtCore.Qt.white

        pen1 = QtGui.QPen(color, 4)

        # TODO: Dont forget that disr segments can also have parent type not CornerItem
        if type(self.startNode.parent) is CornerItem:
            x1 = self.startNode.firstNode().parent
        else:
            x1 = self.startNode.parent

        if type(self.endNode.parent) is CornerItem:
            x2 = self.endNode.lastNode().parent
        else:
            x2 = self.endNode.parent

        # At init
        self.linearGrad = QLinearGradient(
            QPointF(x1.fromPort.scenePos().x(), x1.fromPort.scenePos().y()),
            QPointF(x2.toPort.scenePos().x(), x2.toPort.scenePos().y()),
        )
        self.linearGrad.setColorAt(0, QtCore.Qt.blue)
        self.linearGrad.setColorAt(1, QtCore.Qt.red)

        self.linearGrad.setColorAt(0, QtCore.Qt.gray)
        self.linearGrad.setColorAt(1, QtCore.Qt.black)

        pen1.setBrush(QBrush(self.linearGrad))

        self.singleLine.setPen(pen1)

    def updateGrad(self):
        """
        Updates the gradient by calling the interpolation function
        Returns
        -------

        """
        # This color is overwritten by the gradient
        color = QtCore.Qt.white
        pen1 = QtGui.QPen(color, 4)

        totLenConn = self.parent.totalLength()
        partLen1 = self.parent.partialLength(self.startNode)
        partLen2 = self.parent.partialLength(self.endNode)

        # self.logger.debug("totlenconn is " + str(totLenConn))
        # self.logger.debug("partlen1 is " + str(partLen1) + "(node1)" + str(self.startNode))
        # self.logger.debug("partlen2  is " + str(partLen2) + "(node2)" + str(self.endNode) +"\n")

        # TODO: Dont forget that disr segments can also have parent type not CornerItem

        if type(self.startNode.parent) is CornerItem:
            # self.logger.debug("In updategrad, startnode parent is corner")
            # self.logger.debug("I have a corner parent, self is " + str(self))

            startGradP = QPointF(self.startNode.parent.scenePos().x(), self.startNode.parent.scenePos().y())
        elif self.startNode.prevN() is None:
            startGradP = QPointF(
                self.startNode.parent.fromPort.scenePos().x(), self.startNode.parent.fromPort.scenePos().y()
            )
        else:
            startGradP = QPointF(self.line().p1().x(), self.line().p1().y())

        if type(self.endNode.parent) is CornerItem:
            # self.logger.debug("In update grad, endnode parent is corner")
            # self.logger.debug("I have a corner parent, self is " + str(self))
            endGradP = QPointF(self.endNode.parent.scenePos().x(), self.endNode.parent.scenePos().y())
        elif self.endNode.nextN() is None:
            endGradP = QPointF(self.endNode.parent.toPort.scenePos().x(), self.endNode.parent.toPort.scenePos().y())
        else:
            endGradP = QPointF(self.line().p2().x(), self.line().p2().y())

        self.linearGrad = QLinearGradient(startGradP, endGradP)

        self.linearGrad.setColorAt(0, self.interpolate(partLen1, totLenConn))
        self.linearGrad.setColorAt(1, self.interpolate(partLen2, totLenConn))

        # self.singleLine.setPen(QtGui.QPen(color, 2))

        pen1.setBrush(QBrush(self.linearGrad))

        self.singleLine.setPen(pen1)

    def setHighlight(self, isHighlight: bool) -> None:
        if isHighlight:
            highlightPen = self._createHighlightPen()
            self.singleLine.setPen(highlightPen)
        else:
            self.updateGrad()
