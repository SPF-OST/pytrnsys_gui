from PyQt5 import QtCore
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QGraphicsEllipseItem

from trnsysGUI.Node import Node

# Using hasattr to detect type of parent of node, better solution needed
# No support for disr segements


class CornerItem(QGraphicsEllipseItem):
    def __init__(self, x, y, r1, r2, prevNode, nextNode, parent=None):
        super(CornerItem, self).__init__(x, y, r1, r2, None)
        print("init pos is " + str(self.pos()))
        self.parent = parent
        self.setBrush(QBrush(QtCore.Qt.black))
        self.node = Node(self, prevNode, nextNode)

        # self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        # self.setFlag(self.ItemIsMovable, False)

        self.posCallbacks = []

    def itemChange(self, change, value):
        # print("Change is " + str(change))
        if change == self.ItemScenePositionHasChanged:
            # print("pos change")

            # print("self has partial lenght " + str(self.parent.partialLength(self)))
            # print("Self is at " + str(self.parent.partialLength(self.node) / (self.parent.totalLength())) + "% of the whole connection")

            nNode = self.node.nextN()
            pNode = self.node.prevN()

            print("Parent is " + str(self.parent))
            positionInArr = self.parent.getNodePos(self)

            segBefore = self.parent.segments[positionInArr]
            segAfter = self.parent.segments[positionInArr + 1]

            # print("Position in arr is" + str(positionInArr))
            # segsBefore.setLine(self.scenePos().x(), self.scenePos().y(), segsBefore.line().p2().x(), segsBefore.line().p2().y())
            # segsBefore.setLine(self.scenePos().x(), self.scenePos().y(), segsBefore.line().p2().x(), segsBefore.line().p2().y())

            if type(nNode.parent) is CornerItem:
                # segAfter.setPen(QPen(Qt.red))

                segAfter.setLine(self.scenePos().x(), self.scenePos().y(), segAfter.line().p2().x(),
                                 segAfter.line().p2().y())

                # elementsAtNextNode = self.scene().items(nNode.parent.scenePos())
                # # print("Type of nNode parent is corner")
                # for e in elementsAtNextNode:
                #     if type(e) is segmentItem:
                #         if e.endNode is nNode:
                #             # print("This is the nnode segment")
                #             e.setLine(self.scenePos().x(), self.scenePos().y(), e.line().p2().x(), e.line().p2().y())

            if type(pNode.parent) is CornerItem:
                # segBefore.setPen(QPen(Qt.blue))

                segBefore.setLine(segBefore.line().p1().x(), segBefore.line().p1().y(), self.scenePos().x(),
                                  self.scenePos().y())

                # elementsAtNextNode = self.scene().items(pNode.parent.scenePos())
                # # print("Type of pNode parent is corner")
                # for e in elementsAtNextNode:
                #     if type(e) is segmentItem:
                #         if e.startNode is pNode:
                #             # print("This is the pnode segment")
                #             e.setLine(e.line().p1().x(), e.line().p1().y(), self.scenePos().x(), self.scenePos().y())

            if hasattr(nNode.parent, "fromPort"):

                # print("The moving node (cornerItem) is " + str(self.node))
                # print("type of nNode is conn")

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
                    #     print("Error, there shouldn't be a empty s or s2")
                    #
                    # s.startNode.setNext(s2.endNode)
                    # s2.endNode.setPrev(s.startNode)
                    #
                    # newS = segmentItem(s.startNode, s2.endNode, s.parent)
                    # newS.setVisible(False)
                    # s.parent.parent.diagramScene.addItem(newS)
                    #
                    # if type(s2.endNode.parent) is Connection:
                    #     print("Line of s is " + str(s.line()))
                    #     print("Line of s2 is " + str(s2.line()))
                    #     newS.setLine(self.scenePos().x(),
                    #                  self.scenePos().y(),
                    #                  s2.line().p2().x(),
                    #                  s2.line().p2().y())
                    #     print("Set pos node to Connection")
                    #
                    # elif type(s2.endNode.parent) is CornerItem:
                    #     newS.setLine(self.scenePos().x(),
                    #                  self.scenePos().y(),
                    #                  s2.line().p2().x(),
                    #                  s2.line().p2().y())
                    #     print("Set pos node to node")
                    #
                    # else:
                    #     pass
                    #
                    # newS.setVisible(True)
                    # s.hide()
                    # s2.hide()
                    # s.parent.segments.remove(s2)
                    # s.parent.segments.remove(s)
                    # # print("Length of segments is " + str(len(segments)))
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
                        # print("nNode is at toPort")
                        tItems = self.scene().items(nNode.parent.toPort.scenePos())

                        for t in tItems:
                            if hasattr(t, "dragged"):
                                if t.endNode is nNode:
                                    t.setLine(self.scenePos().x(), self.scenePos().y(), t.line().p2().x(),
                                              t.line().p2().y())

            if hasattr(pNode.parent, "fromPort"):
                # print("The moving node (cornerItem) is " + str(self.node))
                # print("type of pNode is conn")

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
                    #     print("Error, there shouldn't be a empty s or s2")
                    #
                    # s.startNode.setNext(s2.endNode)
                    # s2.endNode.setPrev(s.startNode)
                    #
                    # newS = segmentItem(s.startNode, s2.endNode, s.parent)
                    # newS.setVisible(False)
                    # s.parent.parent.diagramScene.addItem(newS)
                    #
                    # if type(s2.endNode.parent) is Connection:
                    #     print("Line of s is " + str(s.line()))
                    #     print("Line of s2 is " + str(s2.line()))
                    #     newS.setLine(s.line().p2().x(),
                    #                  s.line().p2().y(), self.scenePos().x(), self.scenePos().y())
                    #
                    #     print("Set pos node to Connection")
                    #
                    # elif type(s2.endNode.parent) is CornerItem:
                    #     newS.setLine(s.line().p1().x(),
                    #                  s.line().p1().y(), self.scenePos().x(), self.scenePos().y())
                    #     print("Set pos node to node")
                    #
                    # else:
                    #     pass
                    #
                    # newS.setVisible(True)
                    # s.hide()
                    # s2.hide()
                    # s.parent.segments.remove(s2)
                    # s.parent.segments.remove(s)
                    # # print("Length of segments is " + str(len(segments)))
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
                        # print("pNode is at fromPort")
                        fItems = self.scene().items(pNode.parent.fromPort.scenePos())

                        for f in fItems:
                            if hasattr(f, "dragged"):
                                if f.startNode is pNode:
                                    f.setLine(f.line().p1().x(), f.line().p1().y(), self.scenePos().x(),
                                              self.scenePos().y())

            for s in self.parent.segments:
                s.updateGrad()

        if change == self.ItemScenePositionHasChanged:
            for cb in self.posCallbacks:
                cb(value)
            return value
        return super(CornerItem, self).itemChange(change, value)
