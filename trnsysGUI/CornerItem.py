# pylint: skip-file
# type: ignore

from PyQt5 import QtCore
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QGraphicsEllipseItem

from trnsysGUI.Node import Node


class CornerItem(QGraphicsEllipseItem):
    def __init__(self, x, y, r1, r2, prevNode, nextNode, parent=None):
        """
        CornerItems represent corners for each Connection.
        When a segmentItem is dragged, it will also move the corners, which will trigger the CornerItem
        itemChange method of Qt. There, the adjacent segments are redrawn.

        Note: Using hasattr to detect type of parent of node, better solution needed
        Note: No support for disr (interrupted) segements

        Parameters
        ----------
        x
        y
        r1 : int
        semi-axis length in x direction
        r2 : int
        semi-axis length in y direction
        prevNode
        nextNode
        parent
        """
        super(CornerItem, self).__init__(x, y, r1, r2, None)

        self.logger = parent.logger

        self.logger.debug("init pos is " + str(self.pos()))
        self.parent = parent
        self.setBrush(QBrush(QtCore.Qt.black))
        self.node = Node(self, prevNode, nextNode)

        self.posCallbacks = []

    def itemChange(self, change, value):
        if change == self.ItemScenePositionHasChanged:

            nextNode = self.node.nextN()
            previousNode = self.node.prevN()

            nodePosInConnection = self.parent.getNodePos(self)

            segmentBefore = self.parent.segments[nodePosInConnection]
            segmentAfter = self.parent.segments[nodePosInConnection + 1]

            if type(nextNode.parent) is CornerItem:
                if segmentAfter.line() is not None:
                    segmentAfter.setLine(self.scenePos().x(), self.scenePos().y(), segmentAfter.line().p2().x(),
                                     segmentAfter.line().p2().y())
                else:
                    self.logger.debug("segmentAfter.line() is None")

            if type(previousNode.parent) is CornerItem:
                if segmentBefore.line() is not None:
                    segmentBefore.setLine(segmentBefore.line().p1().x(), segmentBefore.line().p1().y(),
                                          self.scenePos().x(), self.scenePos().y())
                else:
                    self.logger.debug("segmentBefore.line() is None")

            if hasattr(nextNode.parent, "toPort"):
                if nextNode.nextN() is None and self.node.lastNode() is nextNode:
                    self.logger.debug("nextNode is at 'toPort'")
                    lastSegment = self.parent.segments[-1]
                    lastSegment.setLine(self.scenePos().x(), self.scenePos().y(), nextNode.parent.toPort.scenePos().x(),
                                        nextNode.parent.toPort.scenePos().y())

            if hasattr(previousNode.parent, "fromPort"):
                if previousNode.prevN() is None and self.node.firstNode() is previousNode:
                    self.logger.debug("previousNode is at 'fromPort'")
                    firstSegment = self.parent.segments[0]
                    firstSegment.setLine(previousNode.parent.fromPort.scenePos().x(),
                                         previousNode.parent.fromPort.scenePos().y(), self.scenePos().x(),
                                         self.scenePos().y())

            for segment in self.parent.segments:
                try:
                    segment.updateGrad()
                except:
                    self.logger.warning('Could not update color gradient of pipe.')

            for callback in self.posCallbacks:
                callback(value)
            return value

        return super(CornerItem, self).itemChange(change, value)