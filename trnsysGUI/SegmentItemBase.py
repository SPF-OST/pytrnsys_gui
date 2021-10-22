# pylint: skip-file
# type: ignore

import typing as tp
from math import sqrt


from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsTextItem, QMenu

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


class SegmentItemBase(QGraphicsItemGroup):
    def __init__(self, startNode, endNode, parent: "Connection"):
        """
        A connection is displayed as a chain of segmentItems (stored in Connection.segments)
        Parameters.
        ----------
        startNode
        endNode
        parent: type(parent): Connection
        """

        super().__init__(None)
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

        self.insertInParentSegments()

        self.label = QGraphicsTextItem(self.connection.displayName)
        self.connection.parent.diagramScene.addItem(self.label)
        self.label.setVisible(False)
        self.label.setFlag(self.ItemIsMovable, True)
        self.labelMass = QGraphicsTextItem(self.connection.displayName)
        self.connection.parent.diagramScene.addItem(self.labelMass)
        self.labelMass.setVisible(False)
        self.labelMass.setFlag(self.ItemIsMovable, True)

        self.setToolTip(self.connection.displayName)

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
            return QColor(f1 * c2_r + f2 * c1_r, f1 * c2_g + f2 * c1_g, f1 * c2_b + f2 * c1_b)

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

    def updateGrad(self):
        raise NotImplementedError()

    def insertInParentSegments(self):
        """
        This function inserts the segment in correct order to the segment list of the connection.
        Returns
        -------

        """
        prevSeg = None

        for s in self.connection.segments:
            if s.endNode is self.startNode:
                prevSeg = s

        # Todo: Add support for disr segments

        # if the startNode parent is a connection:
        if not hasattr(self.startNode.parent, "fromPort"):
            self.connection.segments.insert(self.connection.segments.index(prevSeg) + 1, self)
        else:

            self.connection.segments.insert(0, self)

    def mousePressEvent(self, e):

        if e.button() == 1:
            self.keyPr = 1
            self.logger.debug("Setting key to 1")

            self.connection.selectConnection()

            if self.isVertical():
                try:
                    self.oldX = self.startNode.parent.scenePos().x()
                except AttributeError:
                    pass
                else:
                    self.logger.debug("set oldx")

    def mouseMoveEvent(self, e):
        self.logger.debug(self.connection.parent.editorMode)
        if self.keyPr == 1:
            self.logger.debug("moved with button 1")
            newPos = e.pos()

            if self.connection.parent.editorMode == 0:
                if not self._isDraggingInProgress:
                    self.initInMode0()
                else:
                    self.dragInMode0(newPos)

            elif self.connection.parent.editorMode == 1:
                if type(self.startNode.parent) is CornerItem and type(self.endNode.parent) is CornerItem:
                    if not self.startNode.parent.isVisible():
                        self.startNode.parent.setVisible(True)
                    if not self.endNode.parent.isVisible():
                        self.endNode.parent.setVisible(True)
                    if self.isVertical():

                        self.logger.debug("Segment is vertical: %s", self.connection.segments.index(self))
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

            posx1 = self.connection.segments[self.connection.segments.index(self) + 2].line().p2().x()

            self.connection.parent.diagramScene.removeItem(nextS)
            self.connection.segments.remove(nextS)
            self.connection.parent.diagramScene.removeItem(nodeTodelete1.parent)

            indexOfSelf = self.connection.segments.index(self)
            nextVS = self.connection.segments[indexOfSelf + 1]

            self.connection.parent.diagramScene.removeItem(nextVS)
            self.connection.segments.remove(nextVS)
            self.connection.parent.diagramScene.removeItem(nodeTodelete2.parent)

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

            posx1 = self.connection.segments[self.connection.segments.index(self) - 2].line().p1().x()

            self.connection.parent.diagramScene.removeItem(prevS)
            self.connection.segments.remove(prevS)
            self.connection.parent.diagramScene.removeItem(nodeTodelete1.parent)

            indexOfSelf = self.connection.segments.index(self)
            nextVS = self.connection.segments[indexOfSelf - 1]

            self.connection.parent.diagramScene.removeItem(nextVS)
            self.connection.segments.remove(nextVS)
            self.connection.parent.diagramScene.removeItem(nodeTodelete2.parent)

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

        self.connection.parent.diagramScene.removeItem(self)
        self.connection.segments.remove(self)
        self.connection.parent.diagramScene.removeItem(self.startNode.parent)
        self.connection.parent.diagramScene.removeItem(self.endNode.parent)

    def splitSegment(self):
        pass

    def mouseReleaseEvent(self, e):
        # Should be same as below
        # self.scene().removeItem(self)

        if e.button() == 1:
            self.keyPr = 0

            if self.connection.parent.editorMode == 0:
                if self._isDraggingInProgress:
                    self.cornerChild.setFlag(self.ItemSendsScenePositionChanges, True)

                    self.hide()
                    self.connection.segments.remove(self)
                    self.connection.parent.diagramScene.removeItem(self)

            elif self.connection.parent.editorMode == 1:
                if self.isVertical():
                    try:
                        self.oldX
                    except AttributeError:
                        pass
                    else:
                        command = HorizSegmentMoveCommand(self, self.oldX, "Moving segment command")

                        self.connection.parent.parent().undoStack.push(command)
                        self.oldX = self.scenePos().x()

                if self.isHorizontal():
                    if type(self.startNode.parent) is CornerItem and type(self.endNode.parent) is CornerItem:
                        try:

                            nextHorizSeg = self.connection.segments[self.connection.segments.index(self) + 2]
                            prevHorizSeg = self.connection.segments[self.connection.segments.index(self) - 2]
                        except IndexError:
                            self.logger.debug("no next or prev segments")
                        else:
                            if nextHorizSeg.isHorizontal() and int(self.endNode.parent.pos().y() - 10) <= int(
                                nextHorizSeg.line().p2().y()
                            ) <= int(self.endNode.parent.pos().y() + 10):
                                self.deleteNextHorizSeg(False, nextHorizSeg)
                                self.logger.debug("next horizontal")
                                return

                            if prevHorizSeg.isHorizontal() and int(self.startNode.parent.pos().y() - 10) <= int(
                                prevHorizSeg.line().p2().y()
                            ) <= int(self.startNode.parent.pos().y() + 10):
                                self.deletePrevHorizSeg(False, prevHorizSeg)
                                self.logger.debug("previous horizontal")
                                return

                if self.secondCorner is not None:
                    self.logger.debug("Second corner is not none")
                    # if PortItem
                    if hasattr(self.endNode.parent, "fromPort"):
                        segbef = self.connection.segments[self.connection.getNodePos(self.secondCorner.node.prevN().parent)]

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

                        segafter = self.connection.segments[self.connection.getNodePos(self.thirdCorner.node.nextN().parent)]

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


            segments = self.connection.segments
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


            segments = self.connection.segments
            for s in segments:
                if s.endNode is self.end:
                    self.disrAfterSeg = s

            self.disrBeforeSeg = self
            self.disrAfter = True

        else:
            self.end = self.endNode

        rad = 2

        self.cornerChild = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.start, self.end, self.connection)
        self.firstChild = self._createSegment(self.start, self.cornerChild.node)
        self.secondChild = self._createSegment(self.cornerChild.node, self.end)

        self.start.setNext(self.cornerChild.node)
        self.end.setPrev(self.cornerChild.node)

        self.firstChild.setVisible(False)
        self.secondChild.setVisible(False)
        self.cornerChild.setVisible(False)

        self.connection.parent.diagramScene.addItem(self.firstChild)
        self.connection.parent.diagramScene.addItem(self.secondChild)
        self.connection.parent.diagramScene.addItem(self.cornerChild)

        self._isDraggingInProgress = True

    def _initInMode1(self, b):

        rad = 2

        if b:
            if (hasattr(self.startNode.parent, "fromPort")) and (self.startNode.prevN() is None):
                # We are at the toPort.
                # self.end = self.endNode
                # self.start = self.startNode

                self.secondCorner = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self.connection)
                self.thirdCorner = CornerItem(

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
                # self.thirdLine.setVisible(False)

                self.connection.parent.diagramScene.addItem(self.secondCorner)
                self.connection.parent.diagramScene.addItem(self.thirdCorner)
                self.connection.parent.diagramScene.addItem(self.firstLine)
                self.connection.parent.diagramScene.addItem(self.secondLine)
                self.logger.debug("inited")

                self._isDraggingInProgress = True
        else:
            if (hasattr(self.endNode.parent, "fromPort")) and (self.endNode.nextN() is None):
                # We are at the toPort.
                # self.end = self.endNode
                # self.start = self.startNode

                self.secondCorner = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self.connection)
                self.thirdCorner = CornerItem(

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
                # self.thirdLine.setVisible(False)

                self.connection.parent.diagramScene.addItem(self.secondCorner)
                self.connection.parent.diagramScene.addItem(self.thirdCorner)
                self.connection.parent.diagramScene.addItem(self.firstLine)
                self.connection.parent.diagramScene.addItem(self.secondLine)
                self.logger.debug("inited")

                self._isDraggingInProgress = True

    def _createSegment(self, startNode, endNode) -> "SegmentItemBase":
        raise NotImplementedError()


    def isVertical(self):
        return self.line().p1().x() == self.line().p2().x()

    def isHorizontal(self):
        return self.line().p1().y() == self.line().p2().y()

    def dragInMode0(self, newPos):
        p1 = self.line().p1()
        p2 = self.line().p2()

        if len(self.scene().items(newPos)) == 0:

            self.firstChild.setLine(p1.x(), p1.y(), newPos.x(), newPos.y())
            self.secondChild.setLine(newPos.x(), newPos.y(), p2.x(), p2.y())

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
        self.scene().parent().showSegmentDlg(self)

    def printItemsAt(self):
        self.logger.debug("Items at startnode are %s", str(self.scene().items(self.line().p1())))
        self.logger.debug("Items at endnode are %s", str(self.scene().items(self.line().p2())))

        for s in self.connection.segments:
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

        a2.triggered.connect(self.connection.deleteConnCom)

        a3 = menu.addAction("Invert this connection")

        a3.triggered.connect(self.connection.invertConnection)

        editHydraulicLoopAction = menu.addAction("Edit hydraulic loop")
        editHydraulicLoopAction.triggered.connect(self.connection.editHydraulicLoop)

        a4 = menu.addAction("Toggle name")

        a4.triggered.connect(self.connection.toggleLabelVisible)

        a5 = menu.addAction("Toggle mass flow")

        a5.triggered.connect(self.connection.toggleMassFlowLabelVisible)

        menu.exec(event.screenPos())

    def configGroup(self):

        GroupChooserConnDlg(self.connection, self.connection.parent)

    def printGroup(self):

        self.logger.debug(self.connection.groupName)

    def inspect(self):

        self.connection.selectConnection()
        self.connection.inspectConn()

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


    def setSelect(self, isSelected: bool) -> None:
        raise NotImplementedError()

    @staticmethod

    def _createSelectPen() -> QPen:
        color = QColor(125, 242, 189)
        width = 4

        selectPen = QPen(color, width)
        return selectPen

    def setColorAndWidthAccordingToMassflow(self, color, width):
        raise NotImplementedError()
