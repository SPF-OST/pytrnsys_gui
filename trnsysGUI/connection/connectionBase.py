# pylint: skip-file
# type: ignore

from __future__ import annotations

import math as _math
import typing as _tp

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsTextItem, QUndoCommand

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.hydraulicLoops as _hl
from massFlowSolver import InternalPiping
from trnsysGUI import idGenerator as _id
from trnsysGUI.CornerItem import CornerItem
from trnsysGUI.Node import Node
from trnsysGUI.PortItemBase import PortItemBase
from trnsysGUI.SegmentItemBase import SegmentItemBase
from trnsysGUI.TVentil import TVentil

if _tp.TYPE_CHECKING:
    import trnsysGUI.BlockItem as _bi


def calcDist(p1, p2):
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class ConnectionBase(_mfs.MassFlowNetworkContributorMixin):
    def __init__(self, fromPort: PortItemBase, toPort: PortItemBase, parent):
        self.logger = parent.logger

        self.fromPort = fromPort
        self.toPort = toPort
        self.displayName = None

        self.parent = parent
        self.groupName = ""
        self.setDefaultGroup()

        # Export related
        self.typeNumber = 0
        self.exportConnsString = ""
        self.exportInputName = "0"
        self.exportInitialInput = -1
        self.exportEquations = []
        self._portItemsWithParent: _tp.List[_tp.Tuple[PortItemBase, _bi.BlockItem]] = []

        # Global
        self.id = self.parent.idGen.getID()
        self.connId = self.parent.idGen.getConnID()
        self.trnsysId = self.parent.idGen.getTrnsysID()

        self.segments: _tp.List[SegmentItemBase] = []

        self.isSelected = False

        self.startNode = Node()
        self.endNode = Node()
        self.firstS: _tp.Optional[SegmentItemBase] = None

        self.mass = 0  # comment out
        self.temperature = 0

        self.initNew(parent)

    def _createSegmentItem(self, startNode, endNode):
        raise NotImplementedError()

    def isVisible(self):
        res = True
        for s in self.segments:
            if not s.isVisible():
                res = False

        return res

    # Setter
    def setName(self, newName):
        self.displayName = newName
        for s in self.segments:
            s.label.setPlainText(newName)

    def setMassAndTemperature(self, mass, temp):
        """
        To show the mass and temperature during mass flow visualization
        """
        self.mass = float(mass)
        self.mass = "{:,}".format(self.mass)
        self.temperature = temp
        for s in self.segments:
            s.labelMass.setPlainText("M: %s kg/h   T: %s\u2103" % (self.mass.replace(",", "'"), self.temperature))

    def setDisplayName(self, newName):
        self.displayName = newName
        self.updateSegLabels()

    def setLabelPos(self, tup: _tp.Tuple[float, float]) -> None:
        pos = self._toPoint(tup)
        self.firstS.label.setPos(pos)

    def setMassLabelPos(self, tup: _tp.Tuple[float, float]) -> None:
        pos = self._toPoint(tup)
        self.firstS.labelMass.setPos(pos)

    @staticmethod
    def _toPoint(tup):
        pos = QPointF(tup[0], tup[1])
        return pos

    def setStartPort(self, newStartPort):
        self.fromPort = newStartPort
        self.startPos = newStartPort.scenePos()
        # self.fromPort.posCallbacks.append(self.setStartPos)

    def setEndPort(self, newEndPort):
        self.toPort = newEndPort

    def setStartPos(self):
        pass

    def setEndPos(self):
        pass

    def setColor(self, value, **kwargs):
        col = QColor(0, 0, 0)

        if "mfr" in kwargs:
            if kwargs["mfr"] == "NegMfr":
                col = QColor(0, 0, 255)
            elif kwargs["mfr"] == "ZeroMfr":
                col = QColor(142, 142, 142)  # Gray
            elif kwargs["mfr"] == "min":
                col = QColor(0, 0, 204)  # deep blue
            elif kwargs["mfr"] == "max":
                col = QColor(153, 0, 0)  # deep red
            elif kwargs["mfr"] == "minTo25":
                col = QColor(0, 128, 255)  # blue
            elif kwargs["mfr"] == "25To50":
                col = QColor(102, 255, 255)  # light blue
            elif kwargs["mfr"] == "50To75":
                col = QColor(255, 153, 153)  # light red
            elif kwargs["mfr"] == "75ToMax":
                col = QColor(255, 51, 51)  # red
            else:
                col = QColor(255, 0, 0)

            for s in self.segments:
                self.logger.debug("Value: " + str(value))
                s.setColorAndWidthAccordingToMassflow(col, value)

        else:
            self.logger.debug("No color to set in Connection.setColor()")

    # Getters
    def getStartPoint(self):
        return QPointF(self.fromPort.scenePos())

    def getEndPoint(self):
        return QPointF(self.toPort.scenePos())

    def getNodePos(self, searchCorner):

        corners = self.getCorners()

        for i in range(len(corners)):
            if corners[i] == searchCorner:
                # self.logger.debug("Found a corner")
                return i
        self.logger.debug("corner not found is " + str(searchCorner))

        return 0

    def getFirstSeg(self):
        return self.segments[0]

    def getCorners(self):
        res = []

        tempNode = self.startNode.nextN()

        while tempNode.nextN() is not None:
            res.append(tempNode.parent)
            tempNode = tempNode.nextN()

        return res

    def switchPorts(self):
        temp = self.fromPort
        self.fromPort = self.toPort
        self.toPort = temp

    # Initialization
    def initNew(self, parent):

        self.parent = parent

        self.parent.trnsysObj.append(self)

        self.displayName = "Conn" + str(self.connId)

        if self.parent.editorMode == 0:
            self.logger.debug("Creating a new connection in mode 0")
            self.initSegmentM0()
        elif self.parent.editorMode == 1:
            self.logger.debug("Creating a new connection in mode 1")
            self._initializeSingleSegmentConnection()
        else:
            self.logger.debug("No valid mode during creating of connection")

        self.parent.connectionList.append(self)
        self.fromPort.connectionList.append(self)
        self.toPort.connectionList.append(self)

    def initSegmentM0(self):
        self.startNode.setParent(self)
        self.endNode.setParent(self)

        self.startNode.setNext(self.endNode)
        self.endNode.setPrev(self.startNode)

        self.firstS = self._createSegmentItem(self.startNode, self.endNode)

        self.firstS.setLine(self.getStartPoint(), self.getEndPoint())

        self.parent.diagramScene.addItem(self.firstS)

        self.positionLabel()

    def _initializeSingleSegmentConnection(self):
        # Can be rewritten for efficiency etc. (e.g not doing initSegmentM0 and calling niceConn())

        self.startNode.setParent(self)
        self.endNode.setParent(self)

        self.startNode.setNext(self.endNode)
        self.endNode.setPrev(self.startNode)

        self.firstS = self._createSegmentItem(self.startNode, self.endNode)

        self.firstS.setLine(self.getStartPoint(), self.getEndPoint())

        self.parent.diagramScene.addItem(self.firstS)

        self.niceConn()

        self.positionLabel()

    def loadSegments(self, segmentsCorners):
        self.clearConn()

        tempNode = self.startNode

        rad = self.getRadius()

        for x in range(len(segmentsCorners)):
            cor = CornerItem(-rad, -rad, 2 * rad, 2 * rad, tempNode, tempNode.nextN(), self)

            cor.setPos(float(segmentsCorners[x][0]), float(segmentsCorners[x][1]))
            cor.setFlag(cor.ItemSendsScenePositionChanges, True)

            cor.setZValue(100)
            cor.setVisible(True)

            self.parent.diagramScene.addItem(cor)

            cor.node.nextNode.setPrev(cor.node)
            cor.node.prevNode.setNext(cor.node)
            self._createSegmentItem(tempNode, cor.node)

            tempNode = cor.node

            self.printConn()

        self._createSegmentItem(tempNode, tempNode.nextN())

        # self.parent.diagramScene.addItem(lastSeg)

        self.printConn()

        for s in self.segments:
            pos1 = None
            pos2 = None

            if isinstance(s.startNode.parent, ConnectionBase) and s.startNode.prevNode is None:
                # self.logger.debug("startnode is at connection")
                pos1 = s.startNode.parent.fromPort.scenePos().x(), s.startNode.parent.fromPort.scenePos().y()
            if isinstance(s.endNode.parent, ConnectionBase) and s.endNode.nextNode is None:
                # self.logger.debug("endnode is at connection")
                pos2 = s.endNode.parent.toPort.scenePos().x(), s.endNode.parent.toPort.scenePos().y()

            if type(s.startNode.parent) is CornerItem:
                # self.logger.debug("startnode is at corner")
                self.logger.debug(
                    str(s.startNode.parent) + " " + str(s.startNode) + "cor " + str(s.startNode.parent.scenePos())
                )
                pos1 = s.startNode.parent.scenePos().x(), s.startNode.parent.scenePos().y()
            if type(s.endNode.parent) is CornerItem:
                # self.logger.debug("endnode is at corner")
                pos2 = s.endNode.parent.scenePos().x(), s.endNode.parent.scenePos().y()

            self.logger.debug("pos1 is " + str(pos1))
            self.logger.debug("pos2 is " + str(pos2))
            s.setLine(pos1[0], pos1[1], pos2[0], pos2[1])

            self.parent.diagramScene.addItem(s)

        self.firstS = self.segments[0]

        self.positionLabel()

    # Label related
    def setLabelVisible(self, isVisible: bool) -> None:
        self.firstS.setLabelVisible(isVisible)

    def toggleLabelVisible(self) -> None:
        self.firstS.toggleLabelVisible()

    def updateSegLabels(self):
        for s in self.segments:
            s.label.setPlainText(self.displayName)

    def positionLabel(self):
        self.firstS.label.setPos(self.getStartPoint())
        self.firstS.labelMass.setPos(self.getStartPoint())
        self.rotateLabel()

    def rotateLabel(self):
        angle = 0 if self.firstS.isHorizontal() else 90
        self.firstS.label.setRotation(angle)

    def setMassFlowLabelVisible(self, isVisible: bool) -> None:
        self.firstS.setMassFlowLabelVisible(isVisible)

    def toggleMassFlowLabelVisible(self) -> None:
        self.firstS.toggleMassFlowLabelVisible()

    def getRadius(self):
        raise NotImplementedError

    # Makes 90deg angles of connection
    def niceConn(self):
        """
        Creates the segments and corners depending on the side of the fromPort and toPort
        Returns
        -------

        """
        # Here different cases can be implemented using self.PORT.side as sketched on paper
        rad = self.getRadius()

        self.logger.debug(
            "FPort " + str(self.fromPort) + " has side " + str(self.fromPort.side) + " has " + str(self.fromPort.name)
        )
        self.logger.debug(
            "FPort " + str(self.fromPort) + " has side " + str(self.fromPort.side) + " has " + str(self.fromPort.name)
        )

        if (self.fromPort.side == 2) and (self.toPort.side == 2):
            self.fromPort.createdAtSide = 2
            self.toPort.createdAtSide = 2
            self.logger.debug("NiceConn 2 to 2")
            portOffset = 30
            self.clearConn()

            corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
            corner2 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, None, self)
            corner3 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner2.node, None, self)
            corner4 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner3.node, self.endNode, self)

            corner1.node.setNext(corner2.node)
            corner2.node.setNext(corner3.node)
            corner3.node.setNext(corner4.node)

            seg1 = self._createSegmentItem(self.startNode, corner1.node)
            seg2 = self._createSegmentItem(corner1.node, corner2.node)
            seg3 = self._createSegmentItem(corner2.node, corner3.node)
            seg4 = self._createSegmentItem(corner3.node, corner4.node)
            seg5 = self._createSegmentItem(corner4.node, self.endNode)

            self.startNode.setNext(corner1.node)
            self.endNode.setPrev(corner4.node)

            self.parent.diagramScene.addItem(seg1)
            self.parent.diagramScene.addItem(seg2)
            self.parent.diagramScene.addItem(seg3)
            self.parent.diagramScene.addItem(seg4)
            self.parent.diagramScene.addItem(seg5)

            self.parent.diagramScene.addItem(corner1)
            self.parent.diagramScene.addItem(corner2)
            self.parent.diagramScene.addItem(corner3)
            self.parent.diagramScene.addItem(corner4)

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            baseline_h = max(pos1.y(), pos2.y()) + 100.6

            p1 = QPointF(pos1.x() + portOffset, pos1.y())
            p2 = QPointF(p1.x(), baseline_h)
            p3 = QPointF(pos2.x() + portOffset, baseline_h)
            p4 = QPointF(p3.x(), pos2.y())

            seg1.setLine(pos1, p1)
            seg2.setLine(p1, p2)
            seg3.setLine(p2, p3)
            seg4.setLine(p3, p4)
            seg5.setLine(p4, pos2)

            corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
            corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)
            corner3.setFlag(corner3.ItemSendsScenePositionChanges, True)
            corner4.setFlag(corner4.ItemSendsScenePositionChanges, True)

            corner1.setZValue(100)
            corner2.setZValue(100)
            corner3.setZValue(100)
            corner4.setZValue(100)

            corner1.setPos(p1)
            corner2.setPos(p2)
            corner3.setPos(p3)
            corner4.setPos(p4)

        elif (self.fromPort.side == 0) and (self.toPort.side == 0):
            self.fromPort.createdAtSide = 0
            self.toPort.createdAtSide = 0
            self.logger.debug("NiceConn 0 to 0")
            portOffset = 30
            self.clearConn()

            corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
            corner2 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, None, self)
            corner3 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner2.node, None, self)
            corner4 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner3.node, self.endNode, self)

            corner1.node.setNext(corner2.node)
            corner2.node.setNext(corner3.node)
            corner3.node.setNext(corner4.node)

            seg1 = self._createSegmentItem(self.startNode, corner1.node)
            seg2 = self._createSegmentItem(corner1.node, corner2.node)
            seg3 = self._createSegmentItem(corner2.node, corner3.node)
            seg4 = self._createSegmentItem(corner3.node, corner4.node)
            seg5 = self._createSegmentItem(corner4.node, self.endNode)

            self.startNode.setNext(corner1.node)
            self.endNode.setPrev(corner4.node)

            self.parent.diagramScene.addItem(seg1)
            self.parent.diagramScene.addItem(seg2)
            self.parent.diagramScene.addItem(seg3)
            self.parent.diagramScene.addItem(seg4)
            self.parent.diagramScene.addItem(seg5)

            self.parent.diagramScene.addItem(corner1)
            self.parent.diagramScene.addItem(corner2)
            self.parent.diagramScene.addItem(corner3)
            self.parent.diagramScene.addItem(corner4)

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            baseline_h = max(pos1.y(), pos2.y()) + 100.6

            # p1 = QPointF(pos1.x() + 50, pos1.y())
            p1 = QPointF(pos1.x() - portOffset, pos1.y())
            p2 = QPointF(p1.x(), baseline_h)
            p3 = QPointF(pos2.x() - portOffset, baseline_h)
            p4 = QPointF(p3.x(), pos2.y())

            seg1.setLine(pos1, p1)
            seg2.setLine(p1, p2)
            seg3.setLine(p2, p3)
            seg4.setLine(p3, p4)
            seg5.setLine(p4, pos2)

            corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
            corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)
            corner3.setFlag(corner3.ItemSendsScenePositionChanges, True)
            corner4.setFlag(corner4.ItemSendsScenePositionChanges, True)

            corner1.setZValue(100)
            corner2.setZValue(100)
            corner3.setZValue(100)
            corner4.setZValue(100)

            corner1.setPos(p1)
            corner2.setPos(p2)
            corner3.setPos(p3)
            corner4.setPos(p4)

        elif self.fromPort.side == 1:
            self.fromPort.createdAtSide = 1
            # todo :  when rotated, it cause a problem because side gets changed

            self.logger.debug("NiceConn from 1")
            portOffset = 30
            self.clearConn()

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            if pos2.y() <= pos1.y():
                corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, self.endNode, self)

                seg1 = self._createSegmentItem(self.startNode, corner1.node)
                seg2 = self._createSegmentItem(corner1.node, self.endNode)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner1.node)

                self.parent.diagramScene.addItem(seg1)
                self.parent.diagramScene.addItem(seg2)
                self.parent.diagramScene.addItem(corner1)

                p1 = QPointF(pos1.x(), pos2.y() - 0.333)  # position of the connecting node

                seg1.setLine(pos1, p1)
                seg2.setLine(p1, pos2)

                corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
                corner1.setZValue(100)
                self.fromPort.setZValue(100)
                self.toPort.setZValue(100)

                corner1.setPos(p1)
                self.firstS = self.getFirstSeg()

            else:
                self.logger.debug("To port below from port")
                corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
                corner2 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, self.endNode, self)

                corner1.node.setNext(corner2.node)

                seg1 = self._createSegmentItem(self.startNode, corner1.node)
                seg2 = self._createSegmentItem(corner1.node, corner2.node)
                seg3 = self._createSegmentItem(corner2.node, self.endNode)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner2.node)

                self.parent.diagramScene.addItem(seg1)
                self.parent.diagramScene.addItem(seg2)
                self.parent.diagramScene.addItem(seg3)

                self.parent.diagramScene.addItem(corner1)
                self.parent.diagramScene.addItem(corner2)

                offsetPoint = pos1.y() - 15.666

                help_point_1 = QPointF(pos1.x(), offsetPoint)
                help_point_2 = QPointF(pos2.x(), offsetPoint)

                seg1.setLine(pos1, help_point_1)
                seg2.setLine(help_point_1, help_point_2)
                seg3.setLine(help_point_2, pos2)

                self.printConnNodes()
                corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
                corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)

                corner1.setZValue(100)
                corner2.setZValue(100)
                self.fromPort.setZValue(100)
                self.toPort.setZValue(100)

                corner1.setPos(help_point_1)
                corner2.setPos(help_point_2)
                self.firstS = self.getFirstSeg()

        elif self.fromPort.side == 3:
            self.fromPort.createdAtSide = 3

            self.logger.debug("NiceConn from 1")
            portOffset = 30
            self.clearConn()

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            if pos2.y() >= pos1.y():
                corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, self.endNode, self)

                seg1 = self._createSegmentItem(self.startNode, corner1.node)
                seg2 = self._createSegmentItem(corner1.node, self.endNode)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner1.node)

                self.parent.diagramScene.addItem(seg1)
                self.parent.diagramScene.addItem(seg2)
                self.parent.diagramScene.addItem(corner1)

                p1 = QPointF(pos1.x(), pos2.y() - 0.333)  # position of the connecting node

                seg1.setLine(pos1, p1)
                seg2.setLine(p1, pos2)

                corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
                corner1.setZValue(100)
                self.fromPort.setZValue(100)
                self.toPort.setZValue(100)

                corner1.setPos(p1)
                self.firstS = self.getFirstSeg()
            else:
                self.logger.debug("To port above from port")
                corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
                corner2 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, self.endNode, self)

                corner1.node.setNext(corner2.node)

                seg1 = self._createSegmentItem(self.startNode, corner1.node)
                seg2 = self._createSegmentItem(corner1.node, corner2.node)
                seg3 = self._createSegmentItem(corner2.node, self.endNode)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner2.node)

                self.parent.diagramScene.addItem(seg1)
                self.parent.diagramScene.addItem(seg2)
                self.parent.diagramScene.addItem(seg3)

                self.parent.diagramScene.addItem(corner1)
                self.parent.diagramScene.addItem(corner2)

                offsetPoint = pos1.y() + 15.666

                help_point_1 = QPointF(pos1.x(), offsetPoint)
                help_point_2 = QPointF(pos2.x(), offsetPoint)

                seg1.setLine(pos1, help_point_1)
                seg2.setLine(help_point_1, help_point_2)
                seg3.setLine(help_point_2, pos2)

                self.printConnNodes()

                corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
                corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)

                corner1.setZValue(100)
                corner2.setZValue(100)
                self.fromPort.setZValue(100)
                self.toPort.setZValue(100)
                self.logger.debug("Here in niceconn")

                corner1.setPos(help_point_1)
                corner2.setPos(help_point_2)
                self.firstS = self.getFirstSeg()

        else:
            # if((self.fromPort.side == 2) and (self.toPort.side == 0)) or (
            #         (self.fromPort.side == 0) and (self.toPort.side == 2) or (self.fromPort.side == 1) and (
            #         self.toPort.side in [0, 1, 2]) or (self.fromPort.side in [0, 1, 2]) and (self.toPort.side == 1)):
            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            self.fromPort.createdAtSide = self.fromPort.side
            self.toPort.createdAtSide = self.toPort.side
            self.logger.debug("Ports are directed to each other")
            self.clearConn()

            corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
            corner2 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, self.endNode, self)

            corner1.node.setNext(corner2.node)

            seg1 = self._createSegmentItem(self.startNode, corner1.node)
            seg2 = self._createSegmentItem(corner1.node, corner2.node)
            seg3 = self._createSegmentItem(corner2.node, self.endNode)

            self.startNode.setNext(corner1.node)
            self.endNode.setPrev(corner2.node)

            # self.logger.debug("niceConn...")
            self.parent.diagramScene.addItem(seg1)
            self.parent.diagramScene.addItem(seg2)
            self.parent.diagramScene.addItem(seg3)

            self.parent.diagramScene.addItem(corner1)
            self.parent.diagramScene.addItem(corner2)

            midx = pos1.x() + 0.5 * (pos2.x() - pos1.x())

            seg1.setLine(pos1.x(), pos1.y(), midx, pos1.y())
            seg2.setLine(midx, pos1.y(), midx, pos2.y())
            seg3.setLine(midx, pos2.y(), pos2.x(), pos2.y())
            self.printConnNodes()

            corner1.setFlag(corner1.ItemSendsScenePositionChanges, True)
            corner2.setFlag(corner2.ItemSendsScenePositionChanges, True)

            corner1.setZValue(100)
            corner2.setZValue(100)
            self.toPort.setZValue(100)
            self.fromPort.setZValue(100)

            self.logger.debug("Here in niceconn")

            help_point_1 = QPointF(midx, pos1.y())
            help_point_2 = QPointF(midx, pos2.y())

            corner1.setPos(help_point_1)
            corner2.setPos(help_point_2)
            self.firstS = self.getFirstSeg()

            self.logger.debug("Conn has now " + str(self.firstS))

    # Unused
    def buildBridges(self):
        # This function finds the colliding line segments and creates the interrupted line effect

        # Debug:
        # self.logger.debug("Segments in brigdes function is " + str(self.segments))
        # self.logger.debug("Length of segments is " + str(len(self.segments)))
        for s in self.segments:
            col = s.collidingItems()
            # Why do the child segments have again colliding Items?
            # self.logger.debug("Start and end of loop segment is " + str(s.startNode) + " and " + str(s.endNode))
            # self.logger.debug("Col items are " + str(col))

            for c in col:
                if type(c) is SegmentItemBase:
                    # self.logger.debug("There is a segment colliding....")
                    # self.logger.debug("c.hasBridge is " + str(c.hasBridge))
                    # self.logger.debug("s.hasBridge is " + str(s.hasBridge))

                    # Both have no bridge and do not collide at the endpoints:
                    # if (s.hasBridge == False) and (c.hasBridge == False) and (c.endNode is not s.startNode) and (c.startNode is not s.endNode):
                    if (c.endNode is not s.startNode) and (c.startNode is not s.endNode):

                        # self.logger.debug("Self has startnode " + str(s.startNode) + " and endnode " + str(
                        #     s.endNode) + " c has startNode " + str(c.startNode) + " and endnode " + str(c.endNode))

                        qp1 = s.line().p1()
                        qp2 = s.line().p2()
                        qp1_ = c.line().p1()
                        qp2_ = c.line().p2()

                        eps2 = 5
                        if abs(qp1.x() - qp2.x()) < eps2 or abs(qp1_.x() - qp2_.x()) < eps2:
                            self.logger.debug("Can't build bridge because one segment is almost verical")

                        else:

                            node1 = Node()
                            node2 = Node()

                            node1.setPrev(s.startNode)
                            node1.setNext(node2)
                            node2.setPrev(node1)
                            node2.setNext(s.endNode)
                            node1.setParent(self)
                            node2.setParent(self)

                            s.startNode.setNext(node1)
                            s.endNode.setPrev(node2)

                            s.firstChild = self._createSegmentItem(s.startNode, node1)
                            s.secondChild = self._createSegmentItem(node2, s.endNode)

                            s.hasBridge = True
                            c.hasBridge = True
                            s.bridgedSegment = c
                            c.bridgedSegment = s

                            s.firstChild.setVisible(False)
                            s.secondChild.setVisible(False)

                            self.parent.diagramScene.addItem(s.firstChild)
                            self.parent.diagramScene.addItem(s.secondChild)

                            # self.logger.debug("Points are " + str(qp1) + str(qp2) + str(qp1_) + str(qp2_))
                            # eps1 = 1
                            # if (abs(qp2.x() - qp1.x()) > eps1) and (abs(qp2_.x() - qp1_.x()) > eps1) :

                            n1 = (qp1.y() * qp2.x() - qp2.y() * qp1.x()) / (qp2.x() - qp1.x())
                            n2 = (qp1_.y() * qp2_.x() - qp2_.y() * qp1_.x()) / (qp2_.x() - qp1_.x())

                            m1 = (qp2.y() - qp1.y()) / (qp2.x() - qp1.x())
                            m2 = (qp2_.y() - qp1_.y()) / (qp2_.x() - qp1_.x())

                            # self.logger.debug("division by " + str(m1) + "    " + str(m2))
                            collisionPos = QPointF((n1 - n2) / (m2 - m1), m1 * (n1 - n2) / (m2 - m1) + n1)

                            vecp2p1 = qp2 - qp1
                            vecp2p1_ = qp2_ - qp1_

                            normVec = _math.sqrt(vecp2p1.x() ** 2 + vecp2p1.y() ** 2)
                            normVec_ = _math.sqrt(vecp2p1_.x() ** 2 + vecp2p1_.y() ** 2)

                            # Compute angle between lines
                            scalarProd = vecp2p1.x() * vecp2p1_.x() + vecp2p1.y() + vecp2p1_.y()
                            angleBetween = _math.acos(scalarProd / (normVec * normVec_))
                            # self.logger.debug(str(degrees(angleBetween)))

                            # Almost working: if line approaches 90 deg or if lines touch because too steep, problem
                            f = 10
                            distFactor = max(f * 1 / angleBetween, f)
                            # self.logger.debug("distFactor " +  str(distFactor))

                            # normalVec = QPointF(-distFactor/normVec * vecp2p1.y(), distFactor/normVec * vecp2p1.x())
                            normVecp2p1 = QPointF(distFactor / normVec * vecp2p1.x(), distFactor / normVec * vecp2p1.y())

                            # self.logger.debug("vector is " + str(normVecp2p1))
                            # self.logger.debug("collisionpos is " + str(collisionPos))
                            # newPos1 = collisionPos - normalVec
                            # newPos2 = collisionPos + normalVec

                            newPos1 = collisionPos - normVecp2p1
                            newPos2 = collisionPos + normVecp2p1

                            s.firstChild.setLine(qp1.x(), qp1.y(), newPos1.x(), newPos1.y())
                            s.secondChild.setLine(newPos2.x(), newPos2.y(), qp2.x(), qp2.y())

                            s.firstChild.setVisible(True)
                            s.secondChild.setVisible(True)

                            s.hide()

                            self.parent.diagramScene.removeItem(s)
                            self.segments.remove(s)

                            # self.logger.debug("s.bridged element is " + str(s.bridgedSegment))
                            # self.logger.debug("c.bridged element is " + str(c.bridgedSegment))
                            # self.logger.debug(len(self.segments))

    # Delete a connection
    def clearConn(self):
        # Deletes all segments and corners in connection
        # self.logger.debug("Connection was before: ")
        # self.printConnNodes()

        walker = self.endNode

        items = self.parent.diagramScene.items()

        for it in items:
            if isinstance(it, SegmentItemBase):
                if it.startNode.lastNode() is self.endNode or it.startNode.firstNode() is self.startNode:
                    # self.logger.debug("Del segment")
                    self.parent.diagramScene.removeItem(it)
            if type(it) is QGraphicsTextItem:
                if isinstance(it.parent, PortItemBase):
                    self.logger.debug("it has " + str(it.parent()))
                    self.logger.debug("Deleting it")
                    self.parent.diagramScene.removeItem(it)

        for seg in self.segments:
            self.parent.diagramScene.removeItem(seg.label)

        self.segments.clear()

        if walker.prevN() is not self.startNode:
            walker = walker.prevN()

            while walker.prevN() is not self.startNode:
                # self.logger.debug("Del corner...")
                if type(walker.parent) is not ConnectionBase:
                    self.parent.diagramScene.removeItem(walker.parent)
                else:
                    self.logger.debug("Caution, this is a disrupt.")
                walker = walker.prevN()
                # del (walker.nextN())

            if type(walker.parent) is not ConnectionBase:
                self.parent.diagramScene.removeItem(walker.parent)
            else:
                self.logger.debug("Caution.")
                # del walker

            self.startNode.setNext(self.endNode)
            self.endNode.setPrev(self.startNode)

        # self.logger.debug("Connection is now: ")
        # self.printConnNodes()

    def deleteConn(self):
        self.logger.debug("Deleting connection " + self.displayName + " " + str(self))
        self.logger.debug("fromPort is at " + str(self.fromPort.parent.displayName))
        self.logger.debug("toPort is at " + str(self.toPort.parent.displayName))

        self.clearConn()
        self.fromPort.connectionList.remove(self)

        # self.logger.debug("Connectionlist of fromPort after removal is:")
        # [self.logger.debug(c.displayName + ": from " + str(c.fromPort.parent) + " to " + str(c.toPort.parent)) for c in self.fromPort.connectionList ]

        self.toPort.connectionList.remove(self)

        # self.logger.debug("Connectionlist of toPort after removal is:")
        # [self.logger.debug(c.displayName + ": from " + str(c.fromPort.parent) + " to " + str(c.toPort.parent)) for c in self.toPort.connectionList ]

        if self in self.parent.trnsysObj:
            self.parent.trnsysObj.remove(self)
        else:
            self.logger.debug("-------> tr obj are " + str(self.parent.trnsysObj))
            self.logger.debug(self.id)
            self.logger.debug([i.id for i in self.parent.trnsysObj])
            return

        self.removeConnFromGroup()

        self.logger.debug("Removing trnsysObj " + str(self))
        self.parent.connectionList.remove(self)
        del self

    def deleteConnCom(self):
        raise NotImplementedError

    # Gradient related
    def totalLength(self):
        summedLength = 0

        for segment in self.segments:
            summedLength += calcDist(segment.line().p1(), segment.line().p2())
        return summedLength

    def partialLength(self, node):
        # Returns the cummulative length of line up to given node
        # Assumes that segments is ordered correctly!
        res = 0
        # self.logger.debug("Segments has len " + str(len(self.segments)))
        if node == self.startNode:
            return res

        for i in self.segments:
            # self.logger.debug("Adding " + str(calcDist(i.line().p1(), i.line().p2())))
            res += calcDist(i.line().p1(), i.line().p2())
            if i.endNode == node:
                # self.logger.debug("Breaking")
                break

        # self.logger.debug("Node " + str(node) + " has pL " + str(res) + "\n")
        return res

    def updateSegGrads(self):
        for s in self.segments:
            s.updateGrad()

    # Invert connection
    def invertConnection(self):
        # Invert segment list
        self.segments.reverse()

        # Invert nodes
        self.invertNodes()

        # Invert ports
        temp = self.toPort
        self.toPort = self.fromPort
        self.fromPort = temp

        sn = self.startNode
        self.startNode = self.endNode
        self.endNode = sn

        for s in self.segments:
            temp2 = s.startNode
            s.startNode = s.endNode
            s.endNode = temp2

            temp3 = s.firstChild
            s.firstChild = s.secondChild
            s.secondChild = temp3

            s.setLine(s.line().p2().x(), s.line().p2().y(), s.line().p1().x(), s.line().p1().y())

            s.updateGrad()

    def invertNodes(self):
        temp = None
        element = self.startNode

        while element.nextN() is not None:
            temp = element.nextN()
            pr = element.prevN()
            ne = element.nextN()

            element.setNext(pr)
            element.setPrev(ne)
            element = temp

        pr = element.prevN()
        ne = element.nextN()
        element.setNext(pr)
        element.setPrev(ne)

    # Group related
    def setDefaultGroup(self):
        self.setConnToGroup("defaultGroup")

    def setConnToGroup(self, newGroupName):
        self.logger.debug("In setConnToGroup")
        if newGroupName == self.groupName:
            self.logger.debug("Block " + str(self) + str(self.displayName) + "is already in this group")
            return
        else:
            # self.logger.debug("groups is " + str(self.parent.groupList))
            for g in self.parent.groupList:
                self.logger.debug("At group " + str(g.displayName))
                if g.displayName == self.groupName:
                    self.logger.debug("Found the old group")
                    g.itemList.remove(self)
                if g.displayName == newGroupName:
                    self.logger.debug("Found the new group")
                    g.itemList.append(self)

            self.groupName = newGroupName

    def removeConnFromGroup(self):
        for g in self.parent.groupList:
            if g.displayName == self.groupName:
                if self in g.itemList:
                    g.itemList.remove(self)
                else:
                    self.logger.debug("While removing conn from group, groupName is invalid")
            else:
                self.logger.debug("While removeing conn from group, no group with conn.groupName")

    # Select when clicked, deselect when clicked elsewhere
    def selectConnection(self):
        self.deselectOtherConnections()

        for s in self.segments:
            s.setSelect(True)

        self.isSelected = True

        self.setLabelsSelected(True)

    def deselectOtherConnections(self):
        for c in self.parent.connectionList:
            c.deselectConnection()

    def deselectConnection(self):
        for s in self.segments:
            s.updateGrad()

        self.isSelected = False

        self.setLabelsSelected(False)

    def setLabelsSelected(self, isSelected: bool) -> None:
        self._setBold(self.firstS.label, isSelected)
        self._setBold(self.firstS.labelMass, isSelected)

    @staticmethod
    def _setBold(label: QGraphicsTextItem, isBold: bool) -> None:
        originalFontCopy = label.font()
        originalFontCopy.setBold(isBold)
        label.setFont(originalFontCopy)

    # Debug
    def inspectConn(self):
        self.parent.listV.clear()
        self.parent.listV.addItem("Display name: " + self.displayName)
        self.parent.listV.addItem("Group name: " + self.groupName)
        self.parent.listV.addItem("Parent: " + str(self.parent))
        # self.parent.listV.addItem("Position: " + str(self.pos()))
        # self.parent.listV.addItem("Sceneposition: " + str(self.scenePos()))
        self.parent.listV.addItem("fromPort: " + str(self.fromPort) + str(self.fromPort.id))
        self.parent.listV.addItem("toPort: " + str(self.toPort) + str(self.toPort.id))

    def printConn(self):
        self.logger.debug("------------------------------------")
        self.logger.debug("This is the printout of connection: " + self.displayName + str(self))
        self.logger.debug("It has fromPort " + str(self.fromPort))
        self.logger.debug("It has toPort " + str(self.toPort))
        self.logger.debug("It has startNode " + str(self.startNode))
        self.logger.debug("It has endNode " + str(self.endNode))

        # self.printConnNodes()
        self.logger.debug("\n")
        # self.printConnSegs()
        self.logger.debug("It goes from " + self.fromPort.parent.displayName + " to " + self.toPort.parent.displayName)
        self.logger.debug("------------------------------------")

    def printConnNodes(self):
        self.logger.debug("These are the nodes: ")

        element = self.startNode
        while element.nextN() is not None:
            self.logger.debug(
                "Node is "
                + str(element)
                + " has nextNode "
                + str(element.nextN())
                + " has pL "
                + str(self.partialLength(element))
            )
            element = element.nextN()

        self.logger.debug("Node is " + str(element) + " has nextNode " + str(element.nextN()))

    def printConnSegs(self):
        self.logger.debug("These are the segments in order")
        for s in self.segments:
            self.logger.debug(
                "Segment is "
                + str(s)
                + " has global id "
                + str(s.id)
                + " has startnode "
                + str(s.startNode)
                + " endnode "
                + str(s.endNode)
            )

    # Saving / Loading
    def encode(self):
        raise NotImplementedError

    def decode(self, i):
        raise NotImplementedError

    # Export related
    def exportBlackBox(self):
        return "noBlackBoxOutput", []

    def exportPumpOutlets(self):
        return "", 0

    def exportMassFlows(self):
        return "", 0

    def exportDivSetting1(self):
        return "", 0

    def exportDivSetting2(self, nUnit):
        return "", nUnit

    def getInternalPiping(self) -> InternalPiping:
        raise NotImplementedError()

    def _getConnectedRealNode(self, portItem: _mfn.PortItem, internalPiping: _mfs.InternalPiping) -> _tp.Optional[_mfn.RealNodeBase]:
        raise NotImplementedError()

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        raise NotImplementedError()

    def _getPortItemsWithParent(self):
        if type(self.fromPort.parent) is TVentil and self.fromPort in self.fromPort.parent.outputs:
            return [(self.fromPort, self.fromPort.parent), (self.toPort, self.toPort.parent)]

        if type(self.toPort.parent) is TVentil and self.fromPort in self.toPort.parent.outputs:
            return [(self.toPort, self.toPort.parent), (self.fromPort, self.fromPort.parent)]

        return [(self.fromPort, self.fromPort.parent), (self.toPort, self.toPort.parent)]

    def findStoragePort(self, virtualBlock):
        portToPrint = None
        for p in virtualBlock.inputs + virtualBlock.outputs:
            if self in p.connectionList:
                # Found the port of the generated block adjacent to this pipe
                # Assumes 1st connection is with storageTank
                if self.fromPort == p:
                    if self.toPort.connectionList[0].fromPort == self.toPort:
                        portToPrint = self.toPort.connectionList[0].toPort
                    else:
                        portToPrint = self.toPort.connectionList[0].fromPort
                else:
                    if self.fromPort.connectionList[0].fromPort == self.fromPort:
                        portToPrint = self.fromPort.connectionList[0].toPort
                    else:
                        portToPrint = self.fromPort.connectionList[0].fromPort
        return portToPrint

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(self, generator: _id.IdGenerator) -> None:
        pass

    def editHydraulicLoop(self) -> None:
        _hl.showHydraulicLoopDialog(self.fromPort, self.toPort)


class DeleteConnectionCommandBase(QUndoCommand):
    def __init__(self, conn, descr):
        super().__init__(descr)
        self.conn = conn
        self.connFromPort = self.conn.fromPort
        self.connToPort = self.conn.toPort
        self.connParent = self.conn.parent

    def redo(self):
        self.conn.deleteConn()
        self.conn = None

    def undo(self):
        self.conn = ConnectionBase(self.connFromPort, self.connToPort, self.connParent)
