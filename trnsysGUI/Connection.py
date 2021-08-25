# pylint: skip-file
# type: ignore

import typing as _tp
import math as _math

import numpy as np
from PyQt5.QtCore import QLineF, QPointF
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsTextItem, QUndoCommand

import trnsysGUI.BlockItem as _bi
import trnsysGUI.IdGenerator as _id
from trnsysGUI.Collector import Collector
from trnsysGUI.CornerItem import CornerItem
from trnsysGUI.Node import Node
from trnsysGUI.PortItem import PortItem
from trnsysGUI.Pump import Pump
from trnsysGUI.TVentil import TVentil
from trnsysGUI.segmentItem import segmentItem


def calcDist(p1, p2):
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class Connection(object):
    def __init__(self, fromPort: PortItem, toPort: PortItem, parent, **kwargs):
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
        self._portItemsWithParent: _tp.List[_tp.Tuple[PortItem, _bi.BlockItem]] = []

        # Global
        self.id = self.parent.idGen.getID()
        self.connId = self.parent.idGen.getConnID()
        self.trnsysId = self.parent.idGen.getTrnsysID()

        self.segments: _tp.List[segmentItem] = []

        self.startNode = Node()
        self.endNode = Node()
        self.firstS: _tp.Optional[segmentItem] = None

        self.segmentsLoad = None
        self.cornersLoad = None
        self.labelPosLoad = None
        self.labelMassPosLoad = None

        self.mass = 0  # comment out
        self.temperature = 0

        # A new connection is created if there are no kwargs
        if not kwargs:
            self.fromPortId = self.parent.idGen.getID()
            self.toPortId = self.parent.idGen.getID()
            self.initNew(parent)
        else:
            if "loadedConn" in kwargs:
                self.logger.debug("Connection being loaded")
                self.fromPortId = kwargs["fromPortId"]
                self.toPortId = kwargs["toPortId"]
                self.segmentsLoad = kwargs["segmentsLoad"]
                self.cornersLoad = kwargs["cornersLoad"]

                if "labelPos" in kwargs:
                    self.labelPosLoad = kwargs["labelPos"]

                if "labelMassPos" in kwargs:
                    self.labelMassPosLoad = kwargs["labelMassPos"]

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
            s.labelMass.setPlainText("M: %s kg/Hr   T: %s\u2103" % (self.mass.replace(",", "'"), self.temperature))

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
            # elif kwargs["mfr"] == "negMinToLower":
            #     col = QColor(0, 0, 0)  # Black
            # elif kwargs["mfr"] == "negLowerToMedian":
            #     col = QColor(47, 47, 73)  # Lighter black
            # elif kwargs["mfr"] == "negMedianToUpper":
            #     col = QColor(78, 78, 97)  # even lighter black
            # elif kwargs["mfr"] == "negUpperToMax":
            #     col = QColor(100, 100, 114)  # even even lighter black
            # elif kwargs["mfr"] == "negMaxToZero":
            #     col = QColor(115, 115, 124)  # darker than gray
            # elif kwargs["mfr"] == "zeroToMin":
            #     col = QColor(156, 156, 164)  # lighter than gray
            else:
                # PosMfr
                col = QColor(255, 0, 0)

            for s in self.segments:
                self.logger.debug("Value: " + str(value))
                pen1 = QPen(col, value)
                s.setPen(pen1)

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
        # Alternative
        # return corners.index(searchCorner)

    def getFirstSeg(self):
        return self.segments[0]

    def getCorners(self):
        # Returns a list containing all the corners of this connection
        res = []

        tempNode = self.startNode.nextN()

        while tempNode.nextN() is not None:
            res.append(tempNode.parent)
            tempNode = tempNode.nextN()

        # self.logger.debug("getcorners gives " + str(res))
        return res

    # To correct the direction of a connection, unused
    def correctPorts(self):
        if isinstance(self.fromPort.parent, Pump):
            if self.fromPort.name == "i":
                self.switchPorts()

        if isinstance(self.toPort.parent, Pump):
            if self.toPort.name == "o":
                self.switchPorts()

        if isinstance(self.fromPort, Collector):
            if self.fromPort.name == "i":
                self.switchPorts()

        if isinstance(self.toPort, Collector):
            if self.toPort.name == "o":
                self.switchPorts()

        if isinstance(self.fromPort.parent, TVentil):
            self.switchPorts()

    def switchPorts(self):
        temp = self.fromPort
        self.fromPort = self.toPort
        self.toPort = temp

    # Initialization
    def initNew(self, parent):

        self.parent = parent
        # self.logger.debug("Parent is " + str(self.parent))

        # Global
        self.parent.trnsysObj.append(self)

        self.displayName = "Conn" + str(self.connId)

        # global editorMode
        if self.parent.editorMode == 0:
            self.logger.debug("Creating a new connection in mode 0")
            self.initSegmentM0()
        elif self.parent.editorMode == 1:
            self.logger.debug("Creating a new connection in mode 1")
            self.initSegmentM1()
        else:
            self.logger.debug("No valid mode during creating of connection")

        self.parent.connectionList.append(self)
        self.fromPort.connectionList.append(self)
        self.toPort.connectionList.append(self)

        # self.correctPorts()

    def initLoad(self):
        # Called by DiagramEditor when loading connection

        self.logger.debug("Port 1 is " + str(self.fromPort) + "has Id" + str(self.fromPort.id))
        self.logger.debug("Port 2 is " + str(self.toPort))

        # self.parent = loadParent
        self.initSegmentM1()

        self.parent.trnsysObj.append(self)

        self.parent.connectionList.append(self)
        self.fromPort.connectionList.append(self)
        self.toPort.connectionList.append(self)

        if len(self.cornersLoad) > 0:
            self.loadSegments()

        if self.labelPosLoad:
            self.setLabelPos(self.labelPosLoad)

        if self.labelMassPosLoad:
            self.setMassLabelPos(self.labelMassPosLoad)

        # Still not tested
        # self.correctPorts()

    def initSegmentM0(self):
        self.startNode.setParent(self)
        self.endNode.setParent(self)

        self.startNode.setNext(self.endNode)
        self.endNode.setPrev(self.startNode)

        self.firstS = segmentItem(self.startNode, self.endNode, self)

        self.firstS.setLine(QLineF(self.getStartPoint(), self.getEndPoint()))

        self.parent.diagramScene.addItem(self.firstS)

        self.positionLabel()

    def initSegmentM1(self):
        # Can be rewritten for efficiency etc. (e.g not doing initSegmentM0 and calling niceConn())

        self.startNode.setParent(self)
        self.endNode.setParent(self)

        self.startNode.setNext(self.endNode)
        self.endNode.setPrev(self.startNode)

        self.firstS = segmentItem(self.startNode, self.endNode, self)

        self.firstS.setLine(QLineF(self.getStartPoint(), self.getEndPoint()))

        self.parent.diagramScene.addItem(self.firstS)

        self.niceConn()

        self.positionLabel()

    def loadSegments(self):
        self.clearConn()

        self.logger.debug("cornerLoads is " + str(self.cornersLoad))

        tempNode = self.startNode

        self.logger.debug("start node has nn " + str(tempNode.nextNode))
        self.logger.debug(" ")
        rad = 2

        for x in range(len(self.cornersLoad)):
            cor = CornerItem(-rad, -rad, 2 * rad, 2 * rad, tempNode, tempNode.nextN(), self)
            # self.logger.debug("items are now " + str(self.parent.diagramScene.items()))
            self.logger.debug("Corner" + str(cor) + " has  " + str(cor.node))

            cor.setPos(float(self.cornersLoad[x][0]), float(self.cornersLoad[x][1]))
            # cor.setFlags(cor.ItemIsSelectable | cor.ItemIsMovable)
            cor.setFlag(cor.ItemSendsScenePositionChanges, True)

            cor.setZValue(100)
            cor.setVisible(True)

            self.parent.diagramScene.addItem(cor)

            cor.node.nextNode.setPrev(cor.node)
            cor.node.prevNode.setNext(cor.node)
            segmentItem(tempNode, cor.node, self)

            tempNode = cor.node

            self.printConn()

        segmentItem(tempNode, tempNode.nextN(), self)

        # self.parent.diagramScene.addItem(lastSeg)

        self.printConn()

        for s in self.segments:
            pos1 = None
            pos2 = None

            if isinstance(s.startNode.parent, Connection) and s.startNode.prevNode is None:
                # self.logger.debug("startnode is at connection")
                pos1 = s.startNode.parent.fromPort.scenePos().x(), s.startNode.parent.fromPort.scenePos().y()
            if isinstance(s.endNode.parent, Connection) and s.endNode.nextNode is None:
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

            s.setLine(QLineF(pos1[0], pos1[1], pos2[0], pos2[1]))

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

        if self.parent.editorMode == 0:
            vec1 = self.firstS.line().p2() - self.firstS.line().p1()
            vec2 = QPointF(1 / 10 * vec1.x(), 1 / 10 * vec1.y())

            eps = 0.5
            if vec1.x() == 0:
                angleBetween = _math.atan(vec1.y() / eps)
            else:
                angleBetween = _math.atan(vec1.y() / vec1.x())

            d1 = calcDist(QPointF(0, 0), vec1)

            if d1 == 0:
                d1 = eps

            vec3 = QPointF(-5 * angleBetween * vec1.y() / d1, 5 * angleBetween * vec1.x() / d1)
            self.firstS.label.setPos(self.fromPort.pos() + vec2 + vec3)

        elif self.parent.editorMode == 1:
            # self.logger.debug("changing label pos in editor mode 1")
            if self.fromPort.side == 0:
                self.firstS.label.setPos(QPointF(-60, 0))

            # Here the behavior of positioning can be improved
            elif self.fromPort.side in [1, 2, 3]:
                self.firstS.label.setPos(QPointF(20, 0))
        else:
            pass
        if self.segmentsLoad:
            vec1 = np.array(self.segmentsLoad[0][:2])
            vec2 = np.array(self.segmentsLoad[0][2:])
            vec = vec2 - vec1
            # uVec1 = vec1/np.linalg.norm(vec1)
            # uVec2 = vec2/np.linalg.norm(vec2)
            uVec = vec / np.linalg.norm(vec)
            dotProduct = np.dot(np.array([1.0, 0]), uVec)
            angle = np.rad2deg(np.arccos(dotProduct))
            if np.isnan(angle):
                angle = 0
            self.firstS.label.setRotation(-angle)

    def setMassFlowLabelVisible(self, isVisible: bool) -> None:
        self.firstS.setMassFlowLabelVisible(isVisible)

    def toggleMassFlowLabelVisible(self) -> None:
        self.firstS.toggleMassFlowLabelVisible()

    # Makes 90deg angles of connection
    def niceConn(self):
        """
        Creates the segments and corners depending on the side of the fromPort and toPort
        Returns
        -------

        """
        # Here different cases can be implemented using self.PORT.side as sketched on paper
        rad = 2  # 4

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

            seg1 = segmentItem(self.startNode, corner1.node, self)
            seg2 = segmentItem(corner1.node, corner2.node, self)
            seg3 = segmentItem(corner2.node, corner3.node, self)
            seg4 = segmentItem(corner3.node, corner4.node, self)
            seg5 = segmentItem(corner4.node, self.endNode, self)

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

            seg1.setLine(QLineF(pos1, p1))
            seg2.setLine(QLineF(p1, p2))
            seg3.setLine(QLineF(p2, p3))
            seg4.setLine(QLineF(p3, p4))
            seg5.setLine(QLineF(p4, pos2))

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

            seg1 = segmentItem(self.startNode, corner1.node, self)
            seg2 = segmentItem(corner1.node, corner2.node, self)
            seg3 = segmentItem(corner2.node, corner3.node, self)
            seg4 = segmentItem(corner3.node, corner4.node, self)
            seg5 = segmentItem(corner4.node, self.endNode, self)

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

            seg1.setLine(QLineF(pos1, p1))
            seg2.setLine(QLineF(p1, p2))
            seg3.setLine(QLineF(p2, p3))
            seg4.setLine(QLineF(p3, p4))
            seg5.setLine(QLineF(p4, pos2))

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

                seg1 = segmentItem(self.startNode, corner1.node, self)
                seg2 = segmentItem(corner1.node, self.endNode, self)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner1.node)

                self.parent.diagramScene.addItem(seg1)
                self.parent.diagramScene.addItem(seg2)
                self.parent.diagramScene.addItem(corner1)

                p1 = QPointF(pos1.x(), pos2.y() - 0.333)  # position of the connecting node

                seg1.setLine(QLineF(pos1, p1))
                seg2.setLine(QLineF(p1, pos2))

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

                seg1 = segmentItem(self.startNode, corner1.node, self)
                seg2 = segmentItem(corner1.node, corner2.node, self)
                seg3 = segmentItem(corner2.node, self.endNode, self)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner2.node)

                self.printConnNodes()
                self.parent.diagramScene.addItem(seg1)
                self.parent.diagramScene.addItem(seg2)
                self.parent.diagramScene.addItem(seg3)

                self.parent.diagramScene.addItem(corner1)
                self.parent.diagramScene.addItem(corner2)

                offsetPoint = pos1.y() - 15.666

                help_point_1 = QPointF(pos1.x(), offsetPoint)
                help_point_2 = QPointF(pos2.x(), offsetPoint)

                seg1.setLine(QLineF(pos1, help_point_1))
                seg2.setLine(QLineF(help_point_1, help_point_2))
                seg3.setLine(QLineF(help_point_2, pos2))

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

        elif self.fromPort.side == 3:
            self.fromPort.createdAtSide = 3

            self.logger.debug("NiceConn from 1")
            portOffset = 30
            self.clearConn()

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            if pos2.y() >= pos1.y():
                corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, self.endNode, self)

                seg1 = segmentItem(self.startNode, corner1.node, self)
                seg2 = segmentItem(corner1.node, self.endNode, self)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner1.node)

                self.parent.diagramScene.addItem(seg1)
                self.parent.diagramScene.addItem(seg2)
                self.parent.diagramScene.addItem(corner1)

                p1 = QPointF(pos1.x(), pos2.y() - 0.333)  # position of the connecting node

                seg1.setLine(QLineF(pos1, p1))
                seg2.setLine(QLineF(p1, pos2))

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

                seg1 = segmentItem(self.startNode, corner1.node, self)
                seg2 = segmentItem(corner1.node, corner2.node, self)
                seg3 = segmentItem(corner2.node, self.endNode, self)

                self.startNode.setNext(corner1.node)
                self.endNode.setPrev(corner2.node)

                self.printConnNodes()
                self.parent.diagramScene.addItem(seg1)
                self.parent.diagramScene.addItem(seg2)
                self.parent.diagramScene.addItem(seg3)

                self.parent.diagramScene.addItem(corner1)
                self.parent.diagramScene.addItem(corner2)

                offsetPoint = pos1.y() + 15.666

                help_point_1 = QPointF(pos1.x(), offsetPoint)
                help_point_2 = QPointF(pos2.x(), offsetPoint)

                seg1.setLine(QLineF(pos1, help_point_1))
                seg2.setLine(QLineF(help_point_1, help_point_2))
                seg3.setLine(QLineF(help_point_2, pos2))

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

            self.fromPort.createdAtSide = self.fromPort.side
            self.toPort.createdAtSide = self.toPort.side
            self.logger.debug("Ports are directed to each other")
            self.clearConn()

            corner1 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, self.startNode, None, self)
            corner2 = CornerItem(-rad, -rad, 2 * rad, 2 * rad, corner1.node, self.endNode, self)

            corner1.node.setNext(corner2.node)

            seg1 = segmentItem(self.startNode, corner1.node, self)
            seg2 = segmentItem(corner1.node, corner2.node, self)
            seg3 = segmentItem(corner2.node, self.endNode, self)

            self.startNode.setNext(corner1.node)
            self.endNode.setPrev(corner2.node)

            # self.logger.debug("niceConn...")
            self.printConnNodes()
            self.parent.diagramScene.addItem(seg1)
            self.parent.diagramScene.addItem(seg2)
            self.parent.diagramScene.addItem(seg3)

            self.parent.diagramScene.addItem(corner1)
            self.parent.diagramScene.addItem(corner2)

            pos1 = self.fromPort.scenePos()
            pos2 = self.toPort.scenePos()

            midx = pos1.x() + 0.5 * (pos2.x() - pos1.x())

            help_point_1 = QPointF(midx, pos1.y())
            help_point_2 = QPointF(midx, pos2.y())

            seg1.setLine(QLineF(pos1, help_point_1))
            seg2.setLine(QLineF(help_point_1, help_point_2))
            seg3.setLine(QLineF(help_point_2, pos2))

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
                if type(c) is segmentItem:
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

                            s.firstChild = segmentItem(s.startNode, node1, s.parent)
                            s.secondChild = segmentItem(node2, s.endNode, s.parent)

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

                            s.firstChild.setLine(QLineF(qp1.x(), qp1.y(), newPos1.x(), newPos1.y()))
                            s.secondChild.setLine(QLineF(newPos2.x(), newPos2.y(), qp2.x(), qp2.y()))

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
            if type(it) is segmentItem:
                if it.startNode.lastNode() is self.endNode or it.startNode.firstNode() is self.startNode:
                    # self.logger.debug("Del segment")
                    self.parent.diagramScene.removeItem(it)
            if type(it) is QGraphicsTextItem:
                if type(it.parent) is PortItem:
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
                if type(walker.parent) is not Connection:
                    self.parent.diagramScene.removeItem(walker.parent)
                else:
                    self.logger.debug("Caution, this is a disrupt.")
                walker = walker.prevN()
                # del (walker.nextN())

            if type(walker.parent) is not Connection:
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
        command = DeleteConnectionCommand(self, "Delete conn comand")
        self.parent.parent().undoStack.push(command)

    # Gradient related
    def totalLength(self):
        s = self.startNode
        e = self.endNode
        res = 0

        for seg in self.segments:
            res += calcDist(seg.line().p1(), seg.line().p2())
        return res

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

    # Highlight when clicked, unhighlight when clicked elsewhere
    def highlightConn(self):
        self.unhighlightOtherConns()

        for s in self.segments:
            s.setHighlight(True)

        self.setLabelsHighlight(True)

    def unhighlightOtherConns(self):
        for c in self.parent.connectionList:
            c.unhighlightConn()

    def unhighlightConn(self):
        for s in self.segments:
            s.updateGrad()

        self.setLabelsHighlight(False)

    def setLabelsHighlight(self, isHighlight: bool) -> None:
        self._setBold(self.firstS.label, isHighlight)
        self._setBold(self.firstS.labelMass, isHighlight)

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
        self.logger.debug("Encoding a connection")

        dct = {}
        dct[".__ConnectionDict__"] = True
        dct["PortFromID"] = self.fromPort.id
        dct["PortToID"] = self.toPort.id
        dct["ConnDisplayName"] = self.displayName
        dct["ConnID"] = self.id
        dct["ConnCID"] = self.connId
        dct["trnsysID"] = self.trnsysId
        dct["GroupName"] = self.groupName

        segments = []  # Not used, but instead corners[]

        for s in self.segments:
            segmentTupel = (s.line().p1().x(), s.line().p1().y(), s.line().p2().x(), s.line().p2().y())
            segments.append(segmentTupel)
        # self.logger.debug("Segments in encoder is " + str(segments))
        dct["SegmentPositions"] = segments
        if len(self.segments) > 0:
            dct["FirstSegmentLabelPos"] = self.segments[0].label.pos().x(), self.segments[0].label.pos().y()
            dct["FirstSegmentMassFlowLabelPos"] = (
                self.segments[0].labelMass.pos().x(),
                self.segments[0].labelMass.pos().y(),
            )
        else:
            self.logger.debug("This connection has no segment")
            defaultPosition = self.fromPort.pos().x(), self.fromPort.pos().y()
            dct["FirstSegmentLabelPos"] = defaultPosition
            dct["FirstSegmentMassFlowLabelPos"] = defaultPosition

        corners = []

        for s in self.getCorners():
            cornerTupel = (s.pos().x(), s.pos().y())
            corners.append(cornerTupel)
        dct["CornerPositions"] = corners
        dictName = "Connection-"

        return dictName, dct

    def decode(self, i):
        self.logger.debug("Loading a connection in Decoder")

        self.id = i["ConnID"]
        self.connId = i["ConnCID"]
        self.trnsysId = i["trnsysID"]
        self.setName(i["ConnDisplayName"])
        self.groupName = "defaultGroup"
        self.setConnToGroup(i["GroupName"])

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

    def exportParametersFlowSolver(self, descConnLength):
        f = ""

        if hasattr(self.fromPort.parent, "getSubBlockOffset"):
            temp = str(self.fromPort.parent.trnsysId + self.fromPort.parent.getSubBlockOffset(self)) + " "
        else:
            portId = self.fromPort.parent.getFlowSolverParametersId(self.fromPort)
            temp = f"{portId} "

        if hasattr(self.toPort.parent, "getSubBlockOffset"):
            temp += str(self.toPort.parent.trnsysId + self.toPort.parent.getSubBlockOffset(self))
        else:
            portId = self.toPort.parent.getFlowSolverParametersId(self.toPort)
            temp += f"{portId} "

        temp += " 0" * 2 + " "
        self.exportConnsString = temp

        # This is to ensure that the "output" of a Div always appears first
        fromPortWithParent = (self.fromPort, self.fromPort.parent)
        if type(self.fromPort.parent) is TVentil and self.fromPort in self.fromPort.parent.outputs:
            self._portItemsWithParent.insert(0, fromPortWithParent)
        else:
            self._portItemsWithParent.append(fromPortWithParent)

        toPortWithParent = (self.toPort, self.toPort.parent)
        if type(self.toPort.parent) is TVentil and self.fromPort in self.toPort.parent.outputs:
            self._portItemsWithParent.insert(0, toPortWithParent)
        else:
            self._portItemsWithParent.append(toPortWithParent)

        f += temp + " " * (descConnLength - len(temp)) + "!" + str(self.trnsysId) + " : " + str(self.displayName) + "\n"

        return f

    @staticmethod
    def exportInputsFlowSolver1():
        return "0,0 ", 1

    def exportInputsFlowSolver2(self):
        return str(self.exportInitialInput) + " ", 1

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        equation1 = self._createFlowSolverOutputEquation(0, abc, prefix, equationNumber, simulationUnit)
        equation2 = self._createFlowSolverOutputEquation(1, abc, prefix, equationNumber, simulationUnit)

        self.exportEquations.append(equation1)
        self.exportEquations.append(equation2)

        equations = equation1 + equation2
        nEquationsUsed = 2
        nextEquationNumber = equationNumber + 3

        return equations, nextEquationNumber, nEquationsUsed

    def _createFlowSolverOutputEquation(self, equationNumber, abc, prefix, equationNumberOffset, simulationUnit):
        return f"{prefix}{self.displayName}_{abc[equationNumber]}=[{simulationUnit},{equationNumberOffset + equationNumber}]\n"

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        f = ""
        unitNumber = startingUnit
        typeNr2 = 931  # Temperature calculation from a pipe

        unitText = ""
        ambientT = 20

        densityVar = "RhoWat"
        specHeatVar = "CPWat"

        equationConstant1 = 1
        equationConstant2 = 3

        parameterNumber = 6
        inputNumbers = 4

        # Fixed strings
        diameterPrefix = "di"
        lengthPrefix = "L"
        lossPrefix = "U"
        tempRoomVar = "TRoomStore"
        initialValueS = "20 0.0 20 20"
        powerPrefix = "P"

        # Momentarily hardcoded
        equationNr = 3

        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
        unitText += "!" + self.displayName + "\n"
        unitText += "PARAMETERS " + str(parameterNumber) + "\n"

        unitText += diameterPrefix + self.displayName + "\n"
        unitText += lengthPrefix + self.displayName + "\n"
        unitText += lossPrefix + self.displayName + "\n"
        unitText += densityVar + "\n"
        unitText += specHeatVar + "\n"
        unitText += str(ambientT) + "\n"

        unitText += "INPUTS " + str(inputNumbers) + "\n"

        if len(self._portItemsWithParent) == 2:
            portItem = self._portItemsWithParent[0][0]
            parent = self._portItemsWithParent[0][1]
            if hasattr(parent, "getSubBlockOffset"):
                unitText += (
                    "T"
                    + parent.displayName
                    + "X"
                    + str(parent.getSubBlockOffset(self) + 1)
                    + "\n"
                )
            else:
                unitText += parent.getTemperatureVariableName(portItem) + "\n"

            unitText += self.exportEquations[0][0 : self.exportEquations[0].find("=")] + "\n"
            unitText += tempRoomVar + "\n"

            portItem = self._portItemsWithParent[1][0]
            parent = self._portItemsWithParent[1][1]
            if hasattr(parent, "getSubBlockOffset"):
                unitText += (
                    "T"
                    + parent.displayName
                    + "X"
                    + str(parent.getSubBlockOffset(self) + 1)
                    + "\n"
                )
            else:
                unitText += parent.getTemperatureVariableName(portItem) + "\n"

        else:
            f += (
                "Error: NO VALUE\n" * 3
                + "at connection with parents "
                + str(self.fromPort.parent)
                + str(self.toPort.parent)
                + "\n"
            )

        unitText += "***Initial values\n"
        unitText += initialValueS + "\n\n"

        unitText += "EQUATIONS " + str(equationNr) + "\n"
        unitText += "T" + self.displayName + "= [" + str(unitNumber) + "," + str(equationConstant1) + "]\n"
        unitText += (
            powerPrefix
            + self.displayName
            + "_kW"
            + "= ["
            + str(unitNumber)
            + ","
            + str(equationConstant2)
            + "]/3600 !kW\n"
        )
        unitText += "Mfr" + self.displayName + "= " + "Mfr" + self.displayName + "_A" "\n"

        unitNumber += 1
        unitText += "\n"
        f += unitText

        return unitText, unitNumber

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

    def cleanUpAfterTrnsysExport(self):
        self.exportConnsString = ""
        self.exportInputName = "0"
        # self.exportInitialInput = -1
        self.exportEquations = []
        self._portItemsWithParent = []

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(self, generator: _id.IdGenerator) -> None:
        pass


class DeleteConnectionCommand(QUndoCommand):
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
        self.conn = Connection(self.connFromPort, self.connToPort, self.connParent)
