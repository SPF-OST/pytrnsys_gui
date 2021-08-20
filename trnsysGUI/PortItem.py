# pylint: skip-file
# type: ignore

import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QColor, QBrush, QCursor, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem, QMenu


class PortItem(QGraphicsEllipseItem):
    def __init__(self, name, side, parent):
        self.parent = parent

        self.logger = parent.logger

        self.name = name
        self.side = side
        self.createdAtSide = side
        self.posCallbacks = []
        self.connectionList = []
        self.id = self.parent.parent.parent().idGen.getID()

        self.color = "white"
        self.ashColorR = QColor(239, 57, 75)
        self.ashColorB = QColor(20, 83, 245)

        QGraphicsEllipseItem.__init__(self, QRectF(-4, -4, 7.0, 7.0), parent)

        self.innerCircle = QGraphicsEllipseItem(-4, -4, 6, 6, self)
        self.innerCircle.setPen(QPen(QColor(0, 0, 0, 0), 0))

        self.visibleColor = QColor(0, 0, 0)

        # This if is only for input/output having different colors
        if name == "i":
            color = QColor(self.ashColorR)
            # self.innerCircle.setBrush(QColor(self.ashColorR))
            # self.innerCircle.setBrush(QColor(0, 0, 0))
            self.innerCircle.setBrush(self.visibleColor)
        if name == "o":
            color = QColor(self.ashColorB)
            # self.innerCircle.setBrush(QColor(self.ashColorB))
            # self.innerCircle.setBrush(QColor(0, 0, 0))
            self.innerCircle.setBrush(self.visibleColor)

        self.setCursor(QCursor(QtCore.Qt.CrossCursor))
        # self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        # The Port itself is larger than only the innerCircle
        self.setBrush(QBrush(QtCore.Qt.white))

        # Hacky fix for no border of ellipse
        p1 = QPen(QColor(0, 0, 0, 0), 0)
        self.setPen(p1)

        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)

        # QUndo framework related
        self.savePos = None
        self.savedPos = False

    def setParent(self, p):
        self.parent = p
        self.setParentItem(p)

    def itemChange(self, change, value):
        # TODO : here to merge segments when moving blockitems
        if (
            self.parent.parent.parent().moveDirectPorts
            and hasattr(self.parent, "heatExchangers")
            and change == self.ItemPositionChange
        ):
            if not self.savePos is None:
                self.logger.debug("val is " + str(value))
                value.setY(max(value.y(), 0))
                value.setY(min(value.y(), self.parent.h))

                return QPointF(self.savePos.x(), value.y())

        if change == self.ItemScenePositionHasChanged and self.parent.parent.parent().editorMode == 0:
            self.logger.debug("editor mode = 0")
            for conn in self.connectionList:
                conn.positionLabel()

                if conn.fromPort is self:
                    # self.logger.debug("This port is the starting port of connection")
                    # nextNodeInConn = conn.startNode.nextN()
                    # self.logger.debug("Type of parent is " + str(type(nextNodeInConn.parent)))

                    e = conn.segments[0]
                    e.setLine(self.scenePos().x(), self.scenePos().y(), e.line().p2().x(), e.line().p2().y())

                if conn.toPort is self:
                    # self.logger.debug("This port is the ending port of connection")
                    # nextNodeInConn = conn.endNode.prevN()
                    # self.logger.debug("nextnodeinconn is " + str(conn.endNode.prevN()))
                    # self.logger.debug("nextNode is " + str(nextNodeInConn))
                    # self.logger.debug("Type of parent is " + str(type(nextNodeInConn.parent)))

                    # New
                    e = conn.segments[-1]
                    e.setLine(e.line().p1().x(), e.line().p1().y(), self.scenePos().x(), self.scenePos().y())

                # global pasting
                if not self.parent.parent.parent().pasting:
                    for s in conn.segments:
                        s.updateGrad()

        if change == self.ItemScenePositionHasChanged and self.parent.parent.parent().editorMode == 1:
            for conn in self.connectionList:
                # Update position of connection label
                conn.positionLabel()

                if conn.fromPort is self:
                    if (self.createdAtSide != 1 and self.createdAtSide != 3) or not conn.segments[0].isVertical():
                        if len(conn.getCorners()) > 0 and len(conn.segments) > 0:
                            self.logger.debug("inside here")
                            cor = conn.getCorners()[0]
                            cor.setPos(cor.pos().x(), self.scenePos().y())

                            seg = conn.segments[0]  # first segment
                            seg.setLine(
                                self.scenePos().x(), self.scenePos().y(), cor.scenePos().x() + 0.6, cor.scenePos().y()
                            )
                            if len(conn.segments) > 2:
                                verSeg = conn.segments[1]
                                nextSeg = conn.segments[2]
                                if nextSeg.isHorizontal() and seg.isHorizontal():
                                    if (
                                        int(seg.endNode.parent.pos().y() - 0)
                                        <= int(nextSeg.line().p2().y())
                                        <= int(seg.endNode.parent.pos().y() + 0)
                                    ):
                                        self.logger.debug("both segments are horizontal from fromport")
                                        # verSeg.deleteSegment()
                                        self.hideCorners(conn)
                                        verSeg.setVisible(False)
                                    else:
                                        self.showCorners(conn)
                                        verSeg.setVisible(True)
                    else:
                        self.logger.debug("inside else")
                        if len(conn.getCorners()) > 0 and len(conn.segments) > 0:
                            cor = conn.getCorners()[0]
                            cor.setPos(self.scenePos().x(), cor.pos().y())

                            seg = conn.segments[0]  # first segment
                            seg.setLine(self.scenePos().x(), self.scenePos().y(), cor.scenePos().x(), cor.scenePos().y())

                elif conn.toPort is self:
                    if (conn.fromPort.createdAtSide != 1 and conn.fromPort.createdAtSide != 3) or not conn.segments[
                        0
                    ].isVertical():
                        if len(conn.getCorners()) > 0 and len(conn.segments) > 0:
                            cor = conn.getCorners()[-1]
                            cor.setPos(cor.pos().x(), self.scenePos().y())

                            seg = conn.segments[-1]
                            seg.setLine(
                                self.scenePos().x(),
                                self.scenePos().y(),
                                cor.scenePos().x() + 0.6,
                                cor.scenePos().y() + 0.6,
                            )
                            if len(conn.segments) > 2:
                                verSeg = conn.segments[-2]
                                nextSeg = conn.segments[-3]
                                if nextSeg.isHorizontal() and seg.isHorizontal():
                                    if (
                                        int(nextSeg.endNode.parent.pos().y() - 0)
                                        <= int(seg.line().p2().y())
                                        <= int(nextSeg.endNode.parent.pos().y() + 0)
                                    ):
                                        self.logger.debug("both segments are horizontal from toport")
                                        self.hideCorners(conn)
                                        verSeg.setVisible(False)
                                    else:
                                        self.showCorners(conn)
                                        verSeg.setVisible(True)
                    else:
                        if len(conn.getCorners()) == 1 and len(conn.segments) > 0:
                            cor = conn.getCorners()[-1]
                            cor.setPos(cor.pos().x(), self.scenePos().y())
                            self.logger.debug("Inside 2nd")

                            seg = conn.segments[-1]  # last segment
                            seg.setLine(self.scenePos().x(), self.scenePos().y(), cor.scenePos().x(), cor.scenePos().y())
                        elif len(conn.getCorners()) == 2 and len(conn.segments) > 0:
                            cor = conn.getCorners()[-1]
                            cor.setPos(self.scenePos().x(), cor.pos().y())
                            self.logger.debug("Inside 3rd")

                            seg = conn.segments[-1]  # last segment
                            seg.setLine(self.scenePos().x(), self.scenePos().y(), cor.scenePos().x(), cor.scenePos().y())

                else:
                    self.logger.debug("Error: In Mode 1, moving a portItem, portItem is neither from nor toPort")

        if change == self.ItemScenePositionHasChanged:
            for cb in self.posCallbacks:
                cb(value)
            return value
        return super(PortItem, self).itemChange(change, value)

    def mousePressEvent(self, event):
        if self.parent.parent.parent().moveDirectPorts and hasattr(self.parent, "heatExchangers"):
            self.setFlag(self.ItemIsMovable)
            self.savePos = self.pos()
        else:
            self.setFlag(self.ItemIsMovable, False)
            self.scene().parent().startConnection(self)

    def hoverEnterEvent(self, event):
        # self.logger.debug("Hovering")

        self.logger.debug(self.parent)

        self.setRect(-4, -4, 10, 10)
        self.innerCircle.setRect(-4, -4, 10, 10)
        if self.name == "i":
            # self.setBrush(Qt.red)
            # self.innerCircle.setBrush(Qt.red)
            # self.innerCircle.setBrush(QColor(0, 0, 0))
            self.innerCircle.setBrush(self.visibleColor)
        if self.name == "o":
            # self.setBrush(QColor(Qt.blue))
            # self.innerCircle.setBrush(QColor(Qt.blue))
            # self.innerCircle.setBrush(QColor(0, 0, 0))
            self.innerCircle.setBrush(self.visibleColor)

        self._debugprint()

    def hoverLeaveEvent(self, event):
        # self.logger.debug("Leaving hover")

        # self.setRect(-6, -6, 12, 12)
        self.setRect(-4, -4, 7, 7)
        self.innerCircle.setRect(-4, -4, 6.5, 6.5)
        if len(self.connectionList) == 0:
            if self.name == "i":
                # self.setBrush(Qt.red)
                # self.setBrush(self.ashColorR)
                # self.innerCircle.setBrush(self.ashColorR)
                # self.innerCircle.setBrush(QColor(0, 0, 0))
                self.innerCircle.setBrush(self.visibleColor)
            if self.name == "o":
                # self.setBrush(self.ashColorR)
                # self.innerCircle.setBrush(self.ashColorB)
                # self.innerCircle.setBrush(QColor(0, 0, 0))
                self.innerCircle.setBrush(self.visibleColor)

        self._debugClear()

    def _debugprint(self):
        self.parent.parent.parent().listV.addItem("This is a PortItem")
        self.parent.parent.parent().listV.addItem("Connections:")
        for c in self.connectionList:
            self.parent.parent.parent().listV.addItem(c.displayName)
        self.parent.parent.parent().listV.addItem(
            "Flipped state (H,V):" + str(self.parent.flippedH) + ", " + str(self.parent.flippedV)
        )
        self.parent.parent.parent().listV.addItem("Side: " + str(self.side))
        self.parent.parent.parent().listV.addItem("createdAtSide: " + str(self.createdAtSide))
        self.parent.parent.parent().listV.addItem("ID: " + str(self.id))
        self.parent.parent.parent().listV.addItem("Block: " + self.parent.displayName)

    def _debugClear(self):
        self.parent.parent.parent().listV.clear()

    def hideCorners(self, connection):
        cor = connection.getCorners()[0]
        cor2 = connection.getCorners()[-1]
        cor.setVisible(False)
        cor2.setVisible(False)

    def showCorners(self, connection):
        cor = connection.getCorners()[0]
        cor2 = connection.getCorners()[-1]
        cor.setVisible(True)
        cor2.setVisible(True)
