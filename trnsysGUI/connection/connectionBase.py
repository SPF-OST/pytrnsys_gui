# pylint: disable = too-many-lines

from __future__ import annotations

import math as _math
import typing as _tp

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsTextItem, QUndoCommand

import trnsysGUI.massFlowSolver as _mfs
from trnsysGUI import idGenerator as _id
from trnsysGUI.CornerItem import CornerItem  # type: ignore[attr-defined]
from trnsysGUI.Node import Node  # type: ignore[attr-defined]
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.SegmentItemBase as _sib


def calcDist(p1, p2):  # pylint: disable = invalid-name
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class ConnectionBase(_mfs.MassFlowNetworkContributorMixin):
    # pylint: disable = too-many-public-methods, too-many-instance-attributes
    def __init__(self, fromPort: _pib.PortItemBase, toPort: _pib.PortItemBase, parent):
        self.logger = parent.logger

        self._fromPort = fromPort
        self._toPort = toPort
        self.displayName = ""

        self.parent = parent

        # Global
        self.id = self.parent.idGen.getID()  # pylint: disable = invalid-name
        self.connId = self.parent.idGen.getConnID()
        self.trnsysId = self.parent.idGen.getTrnsysID()

        self.segments: _tp.List[_sib.SegmentItemBase] = []  # type: ignore[name-defined]

        self.isSelected = False

        self.startNode = Node()
        self.endNode = Node()
        self.firstS: _tp.Optional[_sib.SegmentItemBase] = None  # type: ignore[name-defined]

        self.mass = 0  # comment out
        self.temperature = 0

        self.startPos = None

        self.initNew(parent)

    @property
    def fromPort(self) -> _pib.PortItemBase:
        return self._fromPort

    @property
    def toPort(self) -> _pib.PortItemBase:
        return self._toPort

    def _createSegmentItem(self, startNode, endNode):
        raise NotImplementedError()

    def isVisible(self):
        res = True
        for s in self.segments:  # pylint: disable = invalid-name
            if not s.isVisible():
                res = False

        return res

    def setMassAndTemperature(self, mass, temp):
        """
        To show the mass and temperature during mass flow visualization
        """
        self.mass = float(mass)
        self.mass = f"{self.mass:,}"

        self.temperature = temp
        for s in self.segments:  # pylint: disable = invalid-name
            replacedMass = self.mass.replace(",", "'")
            s.labelMass.setPlainText(f"M: {replacedMass} kg/h   T: {self.temperature}\u2103")

    def setDisplayName(self, newName: str) -> None:
        self.displayName = newName
        self.updateSegLabels()

    def setLabelPos(self, tup: _tp.Tuple[float, float]) -> None:
        pos = self._toPoint(tup)

        assert self.firstS

        self.firstS.label.setPos(pos)

    def setMassLabelPos(self, tup: _tp.Tuple[float, float]) -> None:
        pos = self._toPoint(tup)

        assert self.firstS

        self.firstS.labelMass.setPos(pos)

    @staticmethod
    def _toPoint(tup):
        pos = QPointF(tup[0], tup[1])
        return pos

    def setStartPort(self, newStartPort):
        self.fromPort = newStartPort
        self.startPos = newStartPort.scenePos()

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

            for s in self.segments:  # pylint: disable = invalid-name
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

        for i, corner in enumerate(corners):
            if corner == searchCorner:
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

        self.displayName = "Pi" + self.fromPort.parent.displayName + "_" + self.toPort.parent.displayName

        if self.parent.editorMode == 0:
            self.logger.debug("Creating a new connection in mode 0")
            self._initSegmentM0()
        elif self.parent.editorMode == 1:
            self.logger.debug("Creating a new connection in mode 1")
            self._initializeSingleSegmentConnection()
        else:
            self.logger.debug("No valid mode during creating of connection")

        self.parent.connectionList.append(self)
        self.fromPort.connectionList.append(self)
        self.toPort.connectionList.append(self)

    def _initSegmentM0(self):
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

        for segmentsCorner in segmentsCorners:
            cor = CornerItem(-rad, -rad, 2 * rad, 2 * rad, tempNode, tempNode.nextN(), self)

            cor.setPos(float(segmentsCorner[0]), float(segmentsCorner[1]))
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

        self.printConn()

        for s in self.segments:  # pylint: disable = invalid-name
            pos1 = None
            pos2 = None

            if isinstance(s.startNode.parent, ConnectionBase) and s.startNode.prevNode is None:
                pos1 = s.startNode.parent.fromPort.scenePos().x(), s.startNode.parent.fromPort.scenePos().y()
            if isinstance(s.endNode.parent, ConnectionBase) and s.endNode.nextNode is None:
                pos2 = s.endNode.parent.toPort.scenePos().x(), s.endNode.parent.toPort.scenePos().y()

            if isinstance(s.startNode.parent, CornerItem):
                self.logger.debug(
                    str(s.startNode.parent) + " " + str(s.startNode) + "cor " + str(s.startNode.parent.scenePos())
                )
                pos1 = s.startNode.parent.scenePos().x(), s.startNode.parent.scenePos().y()
            if isinstance(s.endNode.parent, CornerItem):
                pos2 = s.endNode.parent.scenePos().x(), s.endNode.parent.scenePos().y()

            self.logger.debug("pos1 is " + str(pos1))
            self.logger.debug("pos2 is " + str(pos2))
            s.setLine(pos1[0], pos1[1], pos2[0], pos2[1])

            self.parent.diagramScene.addItem(s)

        self.firstS = self.segments[0]

        self.positionLabel()

    # Label related
    def setLabelVisible(self, isVisible: bool) -> None:
        assert self.firstS
        self.firstS.setLabelVisible(isVisible)

    def toggleLabelVisible(self) -> None:
        assert self.firstS
        self.firstS.toggleLabelVisible()

    def updateSegLabels(self):
        for s in self.segments:  # pylint: disable = invalid-name
            s.label.setPlainText(self.displayName)

    def positionLabel(self):
        self.firstS.label.setPos(self.getStartPoint())
        self.firstS.labelMass.setPos(self.getStartPoint())
        self.rotateLabel()

    def rotateLabel(self):
        angle = 0 if self.firstS.isHorizontal() else 90
        self.firstS.label.setRotation(angle)

    def setMassFlowLabelVisible(self, isVisible: bool) -> None:
        assert self.firstS
        self.firstS.setMassFlowLabelVisible(isVisible)

    def toggleMassFlowLabelVisible(self) -> None:
        assert self.firstS
        self.firstS.toggleMassFlowLabelVisible()

    def getRadius(self):
        raise NotImplementedError()

    # Makes 90deg angles of connection
    def niceConn(self):  # pylint: disable = too-many-locals, too-many-statements
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

            baseLineHeight = max(pos1.y(), pos2.y()) + 100.6

            p1 = QPointF(pos1.x() + portOffset, pos1.y())  # pylint: disable = invalid-name
            p2 = QPointF(p1.x(), baseLineHeight)  # pylint: disable = invalid-name
            p3 = QPointF(pos2.x() + portOffset, baseLineHeight)  # pylint: disable = invalid-name
            p4 = QPointF(p3.x(), pos2.y())  # pylint: disable = invalid-name

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

            baseLineHeight = max(pos1.y(), pos2.y()) + 100.6

            p1 = QPointF(pos1.x() - portOffset, pos1.y())  # pylint: disable = invalid-name
            p2 = QPointF(p1.x(), baseLineHeight)  # pylint: disable = invalid-name
            p3 = QPointF(pos2.x() - portOffset, baseLineHeight)  # pylint: disable = invalid-name
            p4 = QPointF(p3.x(), pos2.y())  # pylint: disable = invalid-name

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
            # pylint: disable = fixme
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

                # position of the connecting node
                p1 = QPointF(pos1.x(), pos2.y() - 0.333)  # pylint: disable = invalid-name

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

                help_point_1 = QPointF(pos1.x(), offsetPoint)  # pylint: disable = invalid-name
                help_point_2 = QPointF(pos2.x(), offsetPoint)  # pylint: disable = invalid-name

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

                # position of the connecting node
                p1 = QPointF(pos1.x(), pos2.y() - 0.333)  # pylint: disable = invalid-name

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

                help_point_1 = QPointF(pos1.x(), offsetPoint)  # pylint: disable = invalid-name
                help_point_2 = QPointF(pos2.x(), offsetPoint)  # pylint: disable = invalid-name

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

            help_point_1 = QPointF(midx, pos1.y())  # pylint: disable = invalid-name
            help_point_2 = QPointF(midx, pos2.y())  # pylint: disable = invalid-name

            corner1.setPos(help_point_1)
            corner2.setPos(help_point_2)
            self.firstS = self.getFirstSeg()

            self.logger.debug("Conn has now " + str(self.firstS))

    # Unused
    def buildBridges(self):  # pylint: disable = too-many-locals, too-many-statements
        # This function finds the colliding line segments and creates the interrupted line effect

        for s in self.segments:  # pylint: disable = invalid-name
            col = s.collidingItems()
            # Why do the child segments have again colliding Items?

            for c in col:  # pylint: disable = invalid-name
                if isinstance(c, _sib.SegmentItemBase):
                    # Both have no bridge and do not collide at the endpoints:
                    if (c.endNode is not s.startNode) and (c.startNode is not s.endNode):
                        qp1 = s.line().p1()
                        qp2 = s.line().p2()
                        qp1_ = c.line().p1()  # pylint: disable = invalid-name
                        qp2_ = c.line().p2()  # pylint: disable = invalid-name

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

                            # pylint: disable = invalid-name
                            n1 = (qp1.y() * qp2.x() - qp2.y() * qp1.x()) / (qp2.x() - qp1.x())
                            # pylint: disable = invalid-name
                            n2 = (qp1_.y() * qp2_.x() - qp2_.y() * qp1_.x()) / (qp2_.x() - qp1_.x())

                            m1 = (qp2.y() - qp1.y()) / (qp2.x() - qp1.x())  # pylint: disable = invalid-name
                            m2 = (qp2_.y() - qp1_.y()) / (qp2_.x() - qp1_.x())  # pylint: disable = invalid-name

                            collisionPos = QPointF((n1 - n2) / (m2 - m1), m1 * (n1 - n2) / (m2 - m1) + n1)

                            vecp2p1 = qp2 - qp1  # pylint: disable = invalid-name
                            vecp2p1_ = qp2_ - qp1_  # pylint: disable = invalid-name

                            normVec = _math.sqrt(vecp2p1.x() ** 2 + vecp2p1.y() ** 2)
                            normVec_ = _math.sqrt(vecp2p1_.x() ** 2 + vecp2p1_.y() ** 2)  # pylint:disable=invalid-name

                            # Compute angle between lines
                            scalarProd = vecp2p1.x() * vecp2p1_.x() + vecp2p1.y() + vecp2p1_.y()
                            angleBetween = _math.acos(scalarProd / (normVec * normVec_))

                            # Almost working: if line approaches 90 deg or if lines touch because too steep, problem
                            f = 10  # pylint: disable = invalid-name
                            distFactor = max(f * 1 / angleBetween, f)

                            normVecp2p1 = QPointF(distFactor / normVec * vecp2p1.x(),
                                                  distFactor / normVec * vecp2p1.y())

                            newPos1 = collisionPos - normVecp2p1
                            newPos2 = collisionPos + normVecp2p1

                            s.firstChild.setLine(qp1.x(), qp1.y(), newPos1.x(), newPos1.y())
                            s.secondChild.setLine(newPos2.x(), newPos2.y(), qp2.x(), qp2.y())

                            s.firstChild.setVisible(True)
                            s.secondChild.setVisible(True)

                            s.hide()

                            self.parent.diagramScene.removeItem(s)
                            self.segments.remove(s)

    # Delete a connection
    def clearConn(self):
        # Deletes all segments and corners in connection
        walker = self.endNode

        items = self.parent.diagramScene.items()

        for item in items:
            if isinstance(item, _sib.SegmentItemBase):
                if item.startNode.lastNode() is self.endNode or item.startNode.firstNode() is self.startNode:
                    self.parent.diagramScene.removeItem(item)
            if isinstance(item, QGraphicsTextItem):
                if isinstance(item.parent, _pib.PortItemBase):
                    self.logger.debug("it has " + str(item.parent()))
                    self.logger.debug("Deleting it")
                    self.parent.diagramScene.removeItem(item)

        for seg in self.segments:
            self.parent.diagramScene.removeItem(seg.label)

        self.segments.clear()

        if walker.prevN() is not self.startNode:
            walker = walker.prevN()

            while walker.prevN() is not self.startNode:
                if not isinstance(walker.parent, ConnectionBase):
                    self.parent.diagramScene.removeItem(walker.parent)
                else:
                    self.logger.debug("Caution, this is a disrupt.")
                walker = walker.prevN()

            if not isinstance(walker.parent, ConnectionBase):
                self.parent.diagramScene.removeItem(walker.parent)
            else:
                self.logger.debug("Caution.")

            self.startNode.setNext(self.endNode)
            self.endNode.setPrev(self.startNode)

    def deleteConn(self):
        self.clearConn()
        self.fromPort.connectionList.remove(self)
        self.toPort.connectionList.remove(self)

        if self not in self.parent.trnsysObj:
            return

        self.parent.trnsysObj.remove(self)
        self.parent.connectionList.remove(self)

    def createDeleteUndoCommandAndAddToStack(self) -> None:
        deleteConnectionCommand = self.createDeleteUndoCommand()
        self.parent.parent().undoStack.push(deleteConnectionCommand)

    def createDeleteUndoCommand(self, parentCommand: _tp.Optional[QUndoCommand] = None) -> QUndoCommand:
        raise NotImplementedError()

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
        if node == self.startNode:
            return res

        for i in self.segments:
            res += calcDist(i.line().p1(), i.line().p2())
            if i.endNode == node:
                break

        return res

    def updateSegGrads(self):
        for s in self.segments:  # pylint: disable = invalid-name
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

        startingNode = self.startNode
        self.startNode = self.endNode
        self.endNode = startingNode

        for s in self.segments:  # pylint: disable = invalid-name
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
            previousNode = element.prevN()
            nextNode = element.nextN()

            element.setNext(previousNode)
            element.setPrev(nextNode)
            element = temp

        previousNode = element.prevN()
        nextNode = element.nextN()
        element.setNext(previousNode)
        element.setPrev(nextNode)

    def selectConnection(self):
        for s in self.segments:  # pylint: disable = invalid-name
            s.setSelect(True)

        self.isSelected = True

        self.setLabelsSelected(True)

    def deselectConnection(self):
        for s in self.segments:  # pylint: disable = invalid-name
            s.updateGrad()

        self.isSelected = False

        self.setLabelsSelected(False)

    def setLabelsSelected(self, isSelected: bool) -> None:
        assert self.firstS
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
        self.parent.listV.addItem("Parent: " + str(self.parent))
        self.parent.listV.addItem("fromPort: " + str(self.fromPort) + str(self.fromPort.id))
        self.parent.listV.addItem("toPort: " + str(self.toPort) + str(self.toPort.id))

    def printConn(self):
        self.logger.debug("------------------------------------")
        self.logger.debug("This is the printout of connection: " + self.displayName + str(self))
        self.logger.debug("It has fromPort " + str(self.fromPort))
        self.logger.debug("It has toPort " + str(self.toPort))
        self.logger.debug("It has startNode " + str(self.startNode))
        self.logger.debug("It has endNode " + str(self.endNode))

        self.logger.debug("\n")
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
        for s in self.segments:  # pylint: disable = invalid-name
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
        raise NotImplementedError()

    def decode(self, i):
        raise NotImplementedError()

    # Export related
    def exportBlackBox(self):  # pylint: disable = no-self-use
        return "noBlackBoxOutput", []

    def exportPumpOutlets(self):  # pylint: disable = no-self-use
        return "", 0

    def exportMassFlows(self):  # pylint: disable = no-self-use
        return "", 0

    def exportDivSetting1(self):  # pylint: disable = no-self-use
        return "", 0

    def exportDivSetting2(self, nUnit):  # pylint: disable = no-self-use
        return "", nUnit

    def getInternalPiping(self) -> _mfs.InternalPiping:
        raise NotImplementedError()

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        raise NotImplementedError()

    def findStoragePort(self, virtualBlock):
        portToPrint = None
        for port in virtualBlock.inputs + virtualBlock.outputs:
            if self in port.connectionList:
                # Found the port of the generated block adjacent to this pipe
                # Assumes 1st connection is with storageTank
                if self.fromPort == port:
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
