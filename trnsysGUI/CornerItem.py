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
        # self.logger.debug("Change is " + str(change))
        if change == self.ItemScenePositionHasChanged:
            # self.logger.debug("pos change")
            # self.logger.debug("self has partial lenght " + str(self.parent.partialLength(self)))
            # self.logger.debug("Self is at " + str(self.parent.partialLength(self.node) / (self.parent.totalLength())) + "% of the whole connection")

            nNode = self.node.nextN()
            pNode = self.node.prevN()

            positionInArr = self.parent.getNodePos(self)

            segBefore = self.parent.segments[positionInArr]
            segAfter = self.parent.segments[positionInArr + 1]

            # self.logger.debug("Position in arr is" + str(positionInArr))

            if type(nNode.parent) is CornerItem:
                segAfter.setLine(
                    self.scenePos().x(), self.scenePos().y(), segAfter.line().p2().x(), segAfter.line().p2().y()
                )

            if type(pNode.parent) is CornerItem:
                segBefore.setLine(
                    segBefore.line().p1().x(), segBefore.line().p1().y(), self.scenePos().x(), self.scenePos().y()
                )

            if hasattr(nNode.parent, "fromPort"):
                # self.logger.debug("The moving node (cornerItem) is " + str(self.node))
                # self.logger.debug("type of nNode is conn")

                # We have two options: either nNode is at a port or at a disrupted segment
                if nNode.nextN() is not None:
                    # We are at a disrupted segment
                    pass
                    # segments = nNode.parent.segments
                    #
                    # s = None
                    # s2 = None
                    #
                    # for x in segments:
                    #     if x.endNode is nNode:
                    #         s = x
                    #     if x.startNode is nNode.nextN():
                    #         s2 = x
                    #
                    # if s is None or s2 is None:
                    #     self.logger.debug("Error, there shouldn't be a empty s or s2")
                    #
                    # s.startNode.setNext(s2.endNode)
                    # s2.endNode.setPrev(s.startNode)
                    #
                    # newS = segmentItem(s.startNode, s2.endNode, s.parent)
                    # newS.setVisible(False)
                    # s.parent.parent.diagramScene.addItem(newS)
                    #
                    # if type(s2.endNode.parent) is Connection:
                    #     self.logger.debug("Line of s is " + str(s.line()))
                    #     self.logger.debug("Line of s2 is " + str(s2.line()))
                    #     newS.setLine(self.scenePos().x(),
                    #                  self.scenePos().y(),
                    #                  s2.line().p2().x(),
                    #                  s2.line().p2().y())
                    #     self.logger.debug("Set pos node to Connection")
                    #
                    # elif type(s2.endNode.parent) is CornerItem:
                    #     newS.setLine(self.scenePos().x(),
                    #                  self.scenePos().y(),
                    #                  s2.line().p2().x(),
                    #                  s2.line().p2().y())
                    #     self.logger.debug("Set pos node to node")
                    #
                    # else:
                    #     pass
                    #
                    # newS.setVisible(True)
                    # s.hide()
                    # s2.hide()
                    # s.parent.segments.remove(s2)
                    # s.parent.segments.remove(s)
                    # # self.logger.debug("Length of segments is " + str(len(segments)))
                    #
                    # del s2.endNode
                    # del s.endNode
                    #
                    # newS.parent.parent.diagramScene.removeItem(s)
                    # newS.parent.parent.diagramScene.removeItem(s2)
                    #
                    # newS.parent.buildBridges()

                else:

                    if self.node.lastNode() is nNode:
                        self.logger.debug("nNode is at toPort")
                        t = self.parent.segments[-1]
                        t.setLine(
                            self.scenePos().x(),
                            self.scenePos().y(),
                            nNode.parent.toPort.scenePos().x(),
                            nNode.parent.toPort.scenePos().y(),
                        )

            if hasattr(pNode.parent, "fromPort"):
                # self.logger.debug("The moving node (cornerItem) is " + str(self.node))
                # self.logger.debug("type of pNode is conn")

                if pNode.prevN() is not None:
                    # We are at a disrupted segment
                    pass
                    # segments = nNode.parent.segments
                    #
                    # s = None
                    # s2 = None
                    #
                    # for x in segments:
                    #     if x.startNode is pNode:
                    #         s2 = x
                    #     if x.endNode is pNode.prevN():
                    #         s = x
                    #
                    # if s is None or s2 is None:
                    #     self.logger.debug("Error, there shouldn't be a empty s or s2")
                    #
                    # s.startNode.setNext(s2.endNode)
                    # s2.endNode.setPrev(s.startNode)
                    #
                    # newS = segmentItem(s.startNode, s2.endNode, s.parent)
                    # newS.setVisible(False)
                    # s.parent.parent.diagramScene.addItem(newS)
                    #
                    # if type(s2.endNode.parent) is Connection:
                    #     self.logger.debug("Line of s is " + str(s.line()))
                    #     self.logger.debug("Line of s2 is " + str(s2.line()))
                    #     newS.setLine(s.line().p2().x(),
                    #                  s.line().p2().y(), self.scenePos().x(), self.scenePos().y())
                    #
                    #     self.logger.debug("Set pos node to Connection")
                    #
                    # elif type(s2.endNode.parent) is CornerItem:
                    #     newS.setLine(s.line().p1().x(),
                    #                  s.line().p1().y(), self.scenePos().x(), self.scenePos().y())
                    #     self.logger.debug("Set pos node to node")
                    #
                    # else:
                    #     pass
                    #
                    # newS.setVisible(True)
                    # s.hide()
                    # s2.hide()
                    # s.parent.segments.remove(s2)
                    # s.parent.segments.remove(s)
                    # # self.logger.debug("Length of segments is " + str(len(segments)))
                    #
                    # del s2.endNode
                    # del s.endNode
                    #
                    # newS.parent.parent.diagramScene.removeItem(s)
                    # newS.parent.parent.diagramScene.removeItem(s2)
                    #
                    # newS.parent.buildBridges()

                else:
                    if self.node.firstNode() is pNode:
                        self.logger.debug("pNode is at fromPort")
                        f = self.parent.segments[0]
                        f.setLine(
                            pNode.parent.fromPort.scenePos().x(),
                            pNode.parent.fromPort.scenePos().y(),
                            self.scenePos().x(),
                            self.scenePos().y(),
                        )

            for s in self.parent.segments:
                s.updateGrad()

        if change == self.ItemScenePositionHasChanged:
            for cb in self.posCallbacks:
                cb(value)
            return value
        return super(CornerItem, self).itemChange(change, value)
