# pylint: skip-file
# type: ignore

from math import sqrt
import typing as tp

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QPointF, QLineF
from PyQt5.QtGui import QColor, QLinearGradient, QBrush, QPen
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsTextItem, QMenu

from trnsysGUI.CornerItem import CornerItem
from trnsysGUI.GroupChooserConnDlg import GroupChooserConnDlg
from trnsysGUI.HorizSegmentMoveCommand import HorizSegmentMoveCommand

# This is needed to avoid a circular import but still be able to type check
if tp.TYPE_CHECKING:
    from trnsysGUI.Connection import Connection


def calcDist(p1, p2):
    vec = p1 - p2
    norm = sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class segmentItem(QGraphicsLineItem):
    def __init__(self, startNode, endNode, parent: "Connection"):
        """
        A connection is displayed as a chain of segmentItems (stored in Connection.segments)
        Parameters.
        ----------
        startNode
        endNode
        parent: type(parent): Connection
        """

        super(segmentItem, self).__init__(None)

        self.logger = parent.logger

        self.setFlag(self.ItemIsSelectable, True)

        self.dragged = False
        self.initialised = False
        self.parent = parent

        self.firstChild = None
        self.secondChild = None
        self.cornerChild = None

        self.startNode = startNode
        self.endNode = endNode

        # These nodes are the nodes before and after the crossing
        self.start = None
        self.end = None

        # Unused. Related to interrupting segments for a clearer diagram
        self.disrBeforeNode = None
        self.disrAfterNode = None
        self.disrBeforeSeg = None
        self.disrAfterSeg = None
        self.disrBefore = False
        self.disrAfter = False
        self.hasBridge = False
        self.bridgedSegment = None

        # Only for editorMode 1
        self.firstLine = None
        self.secondLine = None
        self.secondCorner = None
        self.thirdCorner = None

        self.keyPr = 0
        # Used to only create the child objects once
        self._isDraggingInProgress = False

        self.linearGrad = None

        self.insertInParentSegments()
        self.initGrad()

        self.label = QGraphicsTextItem(self.parent.displayName, self.parent.fromPort)
        self.label.setVisible(False)
        self.label.setFlag(self.ItemIsMovable, True)

        self.labelMass = QGraphicsTextItem(self.parent.fromPort)
        self.labelMass.setVisible(False)
        self.labelMass.setFlag(self.ItemIsMovable, True)

        self.setToolTip(self.parent.displayName)

    def segLength(self):
        return calcDist(self.line().p1(), self.line().p2())

    def interpolate(
        self,
        partLen2,
        totLenConn,
    ):
        # c1_r = 0
        # c1_b = 255
        c1_r = 160
        c1_b = 160
        c1_g = 160

        # c2_r = 255
        # c2_b = 0
        c2_r = 0
        c2_b = 0
        c2_g = 0

        try:
            f1 = partLen2 / totLenConn
            f2 = (totLenConn - partLen2) / totLenConn
        except ZeroDivisionError:
            return QColor(100, 100, 100)
        else:
            # return QColor(f1 * c2_r + f2 * c1_r, 0, f1 * c2_b + f2 * c1_b)
            return QColor(f1 * c2_r + f2 * c1_r, f1 * c2_g + f2 * c1_g, f1 * c2_b + f2 * c1_b)

    def initGrad(self):
        """
        Initialize gradient
        Returns
        -------

        """
        # color = QColor(177, 202, 211)
        # color = QColor(3, 124, 193)
        color = QtCore.Qt.red

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

        # self.setPen(QtGui.QPen(color, 2))

        pen1.setBrush(QBrush(self.linearGrad))

        self.setPen(pen1)

    def updateGrad(self):
        """
        Updates the gradient by calling the interpolation function
        Returns
        -------

        """
        # This color is overwritten by the gradient
        color = QtCore.Qt.red
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

        pen1.setBrush(QBrush(self.linearGrad))

        self.setPen(pen1)

    def insertInParentSegments(self):
        """
        This function inserts the segment in correct order to the segment list of the connection.
        Returns
        -------

        """

        prevSeg = None
        for s in self.parent.segments:
            if s.endNode is self.startNode:
                prevSeg = s

        # Todo: Add support for disr segments

        # if the startNode parent is a connection:
        if not hasattr(self.startNode.parent, "fromPort"):
            self.parent.segments.insert(self.parent.segments.index(prevSeg) + 1, self)
        else:
            self.parent.segments.insert(0, self)

    def mousePressEvent(self, e):

        if e.button() == 1:
            self.keyPr = 1
            self.logger.debug("Setting key to 1")

            self.parent.highlightConn()

            if self.isVertical():
                try:
                    self.oldX = self.startNode.parent.scenePos().x()
                except AttributeError:
                    pass
                else:
                    self.logger.debug("set oldx")

    def mouseMoveEvent(self, e):
        # self.logger.debug("mouse moved")
        # self.logger.debug(str(e.button()))

        self.logger.debug(self.parent.parent.editorMode)
        if self.keyPr == 1:
            self.logger.debug("moved with button 1")
            newPos = e.pos()

            if self.parent.parent.editorMode == 0:
                if not self._isDraggingInProgress:
                    self.initInMode0()
                else:
                    self.dragInMode0(newPos)

            elif self.parent.parent.editorMode == 1:
                # if self.parent.segments[0].isVertical() == False and self.parent.segments[2].isVertical() == False:
                # self.logger.debug(len(self.parent.segments))
                if type(self.startNode.parent) is CornerItem and type(self.endNode.parent) is CornerItem:
                    if not self.startNode.parent.isVisible():
                        self.startNode.parent.setVisible(True)
                    if not self.endNode.parent.isVisible():
                        self.endNode.parent.setVisible(True)
                    if self.isVertical():
                        self.logger.debug("Segment is vertical: %s", self.parent.segments.index(self))
                        self.endNode.parent.setPos(newPos.x(), self.endNode.parent.scenePos().y())
                        self.startNode.parent.setPos(newPos.x(), self.startNode.parent.scenePos().y())
                        self.updateGrad()

                    if self.isHorizontal():
                        self.logger.debug("Segment is horizontal")
                        self.endNode.parent.setPos(self.endNode.parent.scenePos().x(), newPos.y())
                        self.startNode.parent.setPos(self.startNode.parent.scenePos().x(), newPos.y())

                elif type(self.endNode.parent) is CornerItem and self.isVertical():
                    self.logger.debug("Segment is vertical and can't be moved")

                if self.isHorizontal():
                    isFirstSegment = hasattr(self.startNode.parent, "fromPort") and not self.startNode.prevN()
                    isLastSegment = hasattr(self.endNode.parent, "fromPort") and not self.endNode.nextN()

                    if isLastSegment:
                        self.logger.debug("A last segment is being dragged.")
                        if not self._isDraggingInProgress:
                            self._initInMode1(False)
                        self._dragInMode1(False, newPos)
                    elif isFirstSegment:
                        self.logger.debug("A first segment is being dragged.")
                        if not self._isDraggingInProgress:
                            self._initInMode1(True)
                        self._dragInMode1(True, newPos)
            else:
                self.logger.debug("Unrecognized editorMode in segmentItem mouseMoveEvent")

    def mouseDoubleClickEvent(self, event):
        # self.parent.deleteConn()
        return

    def deleteNextHorizSeg(self, b, nextS):
        if b:
            pass
        else:
            nodeTodelete1 = self.endNode
            nodeTodelete2 = self.endNode.nextN()
            self.endNode = nextS.endNode

            self.startNode.setNext(self.endNode)
            self.endNode.setPrev(self.startNode)

            # x-position of the ending point of the next segment line
            posx1 = self.parent.segments[self.parent.segments.index(self) + 2].line().p2().x()

            self.parent.parent.diagramScene.removeItem(nextS)
            self.parent.segments.remove(nextS)
            self.parent.parent.diagramScene.removeItem(nodeTodelete1.parent)

            indexOfSelf = self.parent.segments.index(self)
            nextVS = self.parent.segments[indexOfSelf + 1]

            self.parent.parent.diagramScene.removeItem(nextVS)
            self.parent.segments.remove(nextVS)
            self.parent.parent.diagramScene.removeItem(nodeTodelete2.parent)

            self.setLine(
                self.startNode.parent.scenePos().x(),
                self.startNode.parent.scenePos().y(),
                posx1,
                self.startNode.parent.scenePos().y(),
            )

    def deletePrevHorizSeg(self, b, prevS):
        if b:
            pass
        else:
            nodeTodelete1 = self.startNode
            nodeTodelete2 = self.startNode.prevN()
            self.startNode = prevS.startNode

            self.startNode.setNext(self.endNode)
            self.endNode.setPrev(self.startNode)

            posx1 = self.parent.segments[self.parent.segments.index(self) - 2].line().p1().x()

            self.parent.parent.diagramScene.removeItem(prevS)
            self.parent.segments.remove(prevS)
            self.parent.parent.diagramScene.removeItem(nodeTodelete1.parent)

            indexOfSelf = self.parent.segments.index(self)
            nextVS = self.parent.segments[indexOfSelf - 1]

            self.parent.parent.diagramScene.removeItem(nextVS)
            self.parent.segments.remove(nextVS)
            self.parent.parent.diagramScene.removeItem(nodeTodelete2.parent)

            self.setLine(
                posx1,
                self.endNode.parent.scenePos().y(),
                self.endNode.parent.scenePos().x(),
                self.endNode.parent.scenePos().y(),
            )

    def deleteSegment(self):
        nodeToConnect = self.startNode.prevN()
        nodeToConnect2 = self.endNode.nextN()

        nodeToConnect.setNext(nodeToConnect2)

        self.parent.parent.diagramScene.removeItem(self)
        self.parent.segments.remove(self)
        self.parent.parent.diagramScene.removeItem(self.startNode.parent)
        self.parent.parent.diagramScene.removeItem(self.endNode.parent)

    def splitSegment(self):
        pass

    def mouseReleaseEvent(self, e):
        # Should be same as below
        # self.scene().removeItem(self)

        if e.button() == 1:
            self.keyPr = 0

            if self.parent.parent.editorMode == 0:
                if self._isDraggingInProgress:
                    self.cornerChild.setFlag(self.ItemSendsScenePositionChanges, True)

                    self.hide()
                    self.parent.segments.remove(self)
                    self.parent.parent.diagramScene.removeItem(self)

            elif self.parent.parent.editorMode == 1:
                # if self.parent.segments[0].isVertical() == False and self.parent.segments[2].isVertical() == False:
                if self.isVertical():
                    try:
                        self.oldX
                    except AttributeError:
                        pass
                    else:
                        command = HorizSegmentMoveCommand(self, self.oldX, "Moving segment command")
                        self.parent.parent.parent().undoStack.push(command)
                        self.oldX = self.scenePos().x()

                if self.isHorizontal():
                    if type(self.startNode.parent) is CornerItem and type(self.endNode.parent) is CornerItem:
                        try:
                            nextHorizSeg = self.parent.segments[self.parent.segments.index(self) + 2]
                            prevHorizSeg = self.parent.segments[self.parent.segments.index(self) - 2]
                        except IndexError:
                            self.logger.debug("no next or prev segments")
                        else:
                            # if nextHorizSeg.isHorizontal() and int(nextHorizSeg.line().p2().y()) == int(
                            #         self.endNode.parent.pos().y()): # TODO : Edit here to combine segment
                            # self.logger.debug("Next h seg could be deleted")
                            if nextHorizSeg.isHorizontal() and int(self.endNode.parent.pos().y() - 10) <= int(
                                nextHorizSeg.line().p2().y()
                            ) <= int(self.endNode.parent.pos().y() + 10):
                                self.deleteNextHorizSeg(False, nextHorizSeg)
                                self.logger.debug("next horizontal")
                                return

                            if prevHorizSeg.isHorizontal() and int(self.startNode.parent.pos().y() - 10) <= int(
                                prevHorizSeg.line().p2().y()
                            ) <= int(self.startNode.parent.pos().y() + 10):
                                # self.logger.debug("Prev h seg could be deleted")
                                self.deletePrevHorizSeg(False, prevHorizSeg)
                                self.logger.debug("previous horizontal")
                                return

                if self.secondCorner is not None:
                    self.logger.debug("Second corner is not none")
                    # if PortItem
                    if hasattr(self.endNode.parent, "fromPort"):
                        # self.hide()
                        # self.parent.segments.remove(self)
                        # self.parent.parent.diagramScene.removeItem(self)

                        segbef = self.parent.segments[self.parent.getNodePos(self.secondCorner.node.prevN().parent)]

                        segbef.setLine(
                            segbef.line().p1().x(),
                            segbef.line().p1().y(),
                            segbef.line().p2().x(),
                            self.secondCorner.scenePos().y(),
                        )
                        self.setLine(
                            self.thirdCorner.scenePos().x(),
                            self.thirdCorner.scenePos().y(),
                            self.line().p2().x(),
                            self.line().p2().y(),
                        )
                        self.secondCorner.setFlag(self.ItemSendsScenePositionChanges, True)
                        self.thirdCorner.setFlag(self.ItemSendsScenePositionChanges, True)

                        # Allow for iterative branching
                        self.secondCorner = None
                        self.thirdCorner = None
                        self.firstLine = None
                        self.secondLine = None
                        self._isDraggingInProgress = False

                    # if PortItem
                    elif hasattr(self.startNode.parent, "fromPort"):
                        segafter = self.parent.segments[self.parent.getNodePos(self.thirdCorner.node.nextN().parent)]

                        segafter.setLine(
                            segafter.line().p1().x(),
                            self.thirdCorner.scenePos().y(),
                            segafter.line().p2().x(),
                            segafter.line().p2().y(),
                        )
                        self.setLine(
                            self.line().p1().x(),
                            self.line().p1().y(),
                            self.secondCorner.scenePos().x(),
                            self.secondCorner.scenePos().y(),
                        )

                        self.secondCorner.setFlag(self.ItemSendsScenePositionChanges, True)
                        self.thirdCorner.setFlag(self.ItemSendsScenePositionChanges, True)

                        # Allow for iterative branching
                        self.secondCorner = None
                        self.thirdCorner = None
                        self.firstLine = None
                        self.secondLine = None
                        self._isDraggingInProgress = False

                    else:
                        self.logger.debug("getting no start or end")

                else:
                    self.logger.debug("Second corner is none")
            else:
                pass

    def initInMode0(self):
        if (hasattr(self.startNode.parent, "fromPort")) and (self.startNode.prevN() is not None):
            self.disrAfterNode = self.startNode
            self.start = self.startNode.prevN().prevN()

            segments = self.parent.segments
            for s in segments:
                if s.startNode is self.start:
                    self.disrBeforeSeg = s

            self.disrAfterSeg = self
            self.disrBefore = True

        else:
            self.start = self.startNode

        if (hasattr(self.endNode.parent, "fromPort")) and (self.endNode.nextN() is not None):
            self.disrBeforeNode = self.endNode
            self.end = self.endNode.nextN().nextN()

            segments = self.parent.segments
            for s in segments:
                if s.endNode is self.end:
                    self.disrAfterSeg = s

            self.disrBeforeSeg = self
            self.disrAfter = True

        else:
            self.end = self.endNode

        rad = 2

        self.cornerChild = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.start, self.end, self.parent)
        self.firstChild = segmentItem(self.start, self.cornerChild.node, self.parent)
        self.secondChild = segmentItem(self.cornerChild.node, self.end, self.parent)

        self.start.setNext(self.cornerChild.node)
        self.end.setPrev(self.cornerChild.node)

        self.firstChild.setVisible(False)
        self.secondChild.setVisible(False)
        self.cornerChild.setVisible(False)

        self.parent.parent.diagramScene.addItem(self.firstChild)
        self.parent.parent.diagramScene.addItem(self.secondChild)
        self.parent.parent.diagramScene.addItem(self.cornerChild)

        self._isDraggingInProgress = True

    def _initInMode1(self, b):

        rad = 2

        if b:
            if (hasattr(self.startNode.parent, "fromPort")) and (self.startNode.prevN() is None):
                # We are at the toPort.
                # self.end = self.endNode
                # self.start = self.startNode

                self.secondCorner = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self.parent)
                self.thirdCorner = CornerItem(
                    -rad, -rad, 2 * rad, 2 * rad, self.secondCorner.node, self.endNode, self.parent
                )

                self.secondCorner.node.setNext(self.thirdCorner.node)
                self.startNode.setNext(self.secondCorner.node)
                self.endNode.setPrev(self.thirdCorner.node)

                self.endNode = self.secondCorner.node

                self.firstLine = segmentItem(self.secondCorner.node, self.thirdCorner.node, self.parent)
                self.secondLine = segmentItem(self.thirdCorner.node, self.thirdCorner.node.nextN(), self.parent)

                self.secondCorner.setVisible(False)
                self.thirdCorner.setVisible(False)
                self.firstLine.setVisible(False)
                self.secondLine.setVisible(False)
                # self.thirdLine.setVisible(False)

                self.parent.parent.diagramScene.addItem(self.secondCorner)
                self.parent.parent.diagramScene.addItem(self.thirdCorner)
                self.parent.parent.diagramScene.addItem(self.firstLine)
                self.parent.parent.diagramScene.addItem(self.secondLine)
                self.logger.debug("inited")

                self._isDraggingInProgress = True
        else:
            if (hasattr(self.endNode.parent, "fromPort")) and (self.endNode.nextN() is None):
                # We are at the toPort.
                # self.end = self.endNode
                # self.start = self.startNode

                self.secondCorner = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self.parent)
                self.thirdCorner = CornerItem(
                    -rad, -rad, 2 * rad, 2 * rad, self.secondCorner.node, self.endNode, self.parent
                )

                self.secondCorner.node.setNext(self.thirdCorner.node)
                self.startNode.setNext(self.secondCorner.node)
                self.endNode.setPrev(self.thirdCorner.node)

                self.startNode = self.thirdCorner.node

                self.firstLine = segmentItem(self.secondCorner.node.prevN(), self.secondCorner.node, self.parent)
                self.secondLine = segmentItem(self.secondCorner.node, self.thirdCorner.node, self.parent)

                self.secondCorner.setVisible(False)
                self.thirdCorner.setVisible(False)
                self.firstLine.setVisible(False)
                self.secondLine.setVisible(False)
                # self.thirdLine.setVisible(False)

                self.parent.parent.diagramScene.addItem(self.secondCorner)
                self.parent.parent.diagramScene.addItem(self.thirdCorner)
                self.parent.parent.diagramScene.addItem(self.firstLine)
                self.parent.parent.diagramScene.addItem(self.secondLine)
                self.logger.debug("inited")

                self._isDraggingInProgress = True

    def isVertical(self):
        return self.line().p1().x() == self.line().p2().x()

    def isHorizontal(self):
        return self.line().p1().y() == self.line().p2().y()

    def dragInMode0(self, newPos):
        p1 = self.line().p1()
        p2 = self.line().p2()

        if len(self.scene().items(newPos)) == 0:
            self.firstChild.setLine(QLineF(p1.x(), p1.y(), newPos.x(), newPos.y()))
            self.secondChild.setLine(QLineF(newPos.x(), newPos.y(), p2.x(), p2.y()))

            self.cornerChild.setPos(newPos)

            self.firstChild.updateGrad()
            self.secondChild.updateGrad()

            # Bring corner to front
            self.cornerChild.setZValue(100)
            self.firstChild.setZValue(1)
            self.secondChild.setZValue(1)

            self.firstChild.setVisible(True)
            self.secondChild.setVisible(True)
            self.cornerChild.setVisible(True)

    def _dragInMode1(self, b, newPos):
        self.logger.debug("after inited")

        if b:
            self.thirdCorner.setPos(newPos.x() - 10, newPos.y())
            self.secondCorner.setPos(newPos.x() - 10, self.parent.fromPort.scenePos().y())
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
            self.thirdCorner.setPos(newPos.x() + 10, self.parent.toPort.scenePos().y())
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
        # dia = segmentDlg(self, self.scene().parent())
        self.scene().parent().showSegmentDlg(self)

    def printItemsAt(self):
        self.logger.debug("Items at startnode are %s", str(self.scene().items(self.line().p1())))
        self.logger.debug("Items at endnode are %s", str(self.scene().items(self.line().p2())))

        for s in self.parent.segments:
            self.logger.debug(
                "Segment in list is %s has startnode %s endnode %s",
                str(s),
                str(s.startNode.parent),
                str(s.endNode.parent),
            )

    def contextMenuEvent(self, event):
        menu = QMenu()
        a1 = menu.addAction("Rename...")
        a1.triggered.connect(self.renameConn)

        a2 = menu.addAction("Delete this connection")
        a2.triggered.connect(self.parent.deleteConnCom)

        a3 = menu.addAction("Invert this connection")
        a3.triggered.connect(self.parent.invertConnection)

        a4 = menu.addAction("Toggle name")
        a4.triggered.connect(self.parent.toggleLabelVisible)

        a5 = menu.addAction("Toggle mass flow")
        a5.triggered.connect(self.parent.toggleMassFlowLabelVisible)

        # b1 = menu.addAction('Set group ')
        # b1.triggered.connect(self.configGroup)
        # a4 = menu.addAction('Print end and start items')
        # a4.triggered.connect(self.printItemsAt)
        #
        # a5 = menu.addAction('Print corners')
        # a5.triggered.connect(self.parent.getCorners)
        #
        # a6 = menu.addAction('Print group')
        # a6.triggered.connect(self.printGroup)
        #
        # a7 = menu.addAction('Inspect')
        # a7.triggered.connect(self.inspect)
        menu.exec_(event.screenPos())

    def configGroup(self):
        GroupChooserConnDlg(self.parent, self.parent.parent)

    def printGroup(self):
        self.logger.debug(self.parent.groupName)

    def inspect(self):
        self.parent.highlightConn()
        self.parent.inspectConn()

    def setLabelVisible(self, isVisible: bool) -> None:
        self.label.setVisible(isVisible)

    def toggleLabelVisible(self) -> None:
        wasVisible = self.label.isVisible()
        self.setLabelVisible(not wasVisible)

    def setMassFlowLabelVisible(self, isVisible: bool) -> None:
        self.labelMass.setVisible(isVisible)

    def toggleMassFlowLabelVisible(self) -> None:
        wasVisible = self.labelMass.isVisible()
        self.setMassFlowLabelVisible(not wasVisible)

    def setHighlight(self, isHighlight: bool) -> None:
        if isHighlight:
            highlightPen = self._createHighlightPen()
            self.setPen(highlightPen)
        else:
            self.updateGrad()

    @staticmethod
    def _createHighlightPen() -> QPen:
        color = QColor(125, 242, 189)
        width = 4
        highlightPen = QPen(color, width)
        return highlightPen
