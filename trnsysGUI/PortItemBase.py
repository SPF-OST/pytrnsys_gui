# pylint: skip-file
# type: ignore

from __future__ import annotations

import typing as _tp

from PyQt5 import QtCore
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QColor, QBrush, QCursor, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem

if _tp.TYPE_CHECKING:
    import massFlowSolver.networkModel as _mfn
    import massFlowSolver as _mfs
    import trnsysGUI.connection.connectionBase as _cb


class PortItemBase(QGraphicsEllipseItem):
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
            self.innerCircle.setBrush(self.visibleColor)
        if name == "o":
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
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if self.parent.parent.parent().moveDirectPorts and hasattr(self.parent, "heatExchangers"):
            self.setFlag(self.ItemIsMovable)
            self.savePos = self.pos()
            return

        if self.connectionList:
            return

        self.setFlag(self.ItemIsMovable, False)
        self.scene().parent().startConnection(self)

    def hoverEnterEvent(self, event):
        self.logger.debug(self.parent)

        self.enlargePortSize()

        self.highlightInternallyConnectedPortItems()

        self._debugprint()

    def highlightInternallyConnectedPortItems(self):
        from massFlowSolver import search as _search
        internallyConnectedPortItems = list(_search.getInternallyConnectedPortItems(self))
        for portItem in internallyConnectedPortItems:
            portItem.innerCircle.setBrush(self.ashColorB)

    def enlargePortSize(self):
        self.setRect(-4, -4, 10, 10)
        self.innerCircle.setRect(-4, -4, 10, 10)

    def hoverLeaveEvent(self, event):
        self.defaultPortSize()

        self.unhighlightInternallyConnectedPortItems()

        self._debugClear()

    def unhighlightInternallyConnectedPortItems(self):
        from massFlowSolver import search as _search
        internallyConnectedPortItems = list(_search.getInternallyConnectedPortItems(self))
        for portItem in internallyConnectedPortItems:
            portItem.innerCircle.setBrush(self.visibleColor)

    def defaultPortSize(self):
        self.setRect(-4, -4, 7, 7)
        self.innerCircle.setRect(-4, -4, 6.5, 6.5)

    def _debugprint(self):
        self.parent.parent.parent().listV.addItem("ID: " + str(self.id))

        internalPiping = self.parent.getInternalPiping()
        portItemsAndInternalRealNode = internalPiping.getPortItemsAndAdjacentRealNodeForGraphicalPortItem(self)
        portItems = [pr.portItem for pr in portItemsAndInternalRealNode]
        formattedPortItems = [f"{p.name} ({p.type.value})" for p in portItems]
        jointFormattedPortItems = ", ".join(formattedPortItems)
        self.parent.parent.parent().listV.addItem(f"Names: {jointFormattedPortItems}")

        self.parent.parent.parent().listV.addItem("Block: " + self.parent.displayName)

        self.parent.parent.parent().listV.addItem("Connections:")
        for connection in self.connectionList:
            self.parent.parent.parent().listV.addItem(connection.displayName)

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

    def getConnectedRealNode(
        self,
        portItem: _mfn.PortItem,
        massFlowContributor: _mfs.MassFlowNetworkContributorMixin,
    ) -> _tp.Optional[_mfn.RealNodeBase]:
        connectedMassFlowContributor = self._getConnectedMassFlowContributor(massFlowContributor)
        if not connectedMassFlowContributor:
            return None

        connectedInternalPiping = connectedMassFlowContributor.getInternalPiping()

        connectedPortItemsAndAdjacentRealNode = (
            connectedInternalPiping.getPortItemsAndAdjacentRealNodeForGraphicalPortItem(self)
        )

        selectedConnectedRealNode = self._selectConnectedRealNode(portItem, connectedPortItemsAndAdjacentRealNode)

        return selectedConnectedRealNode

    def _getConnectedMassFlowContributor(
        self, massFlowContributor: _mfs.MassFlowNetworkContributorMixin
    ) -> _tp.Optional[_mfs.MassFlowNetworkContributorMixin]:
        if massFlowContributor == self.parent:
            return self._getConnectionOrNone()
        else:
            connection = self._getConnectionOrNone()

            if not connection or connection != massFlowContributor:
                raise ValueError("`massFlowContributor' is not adjacent to this port item.")

            return self.parent

    def _getConnectionOrNone(self) -> _tp.Optional[_cb.ConnectionBase]:
        if not self.connectionList:
            return None

        assert len(self.connectionList) == 1

        connection = self.connectionList[0]

        return connection

    def _selectConnectedRealNode(
        self,
        portItem: _mfn.PortItem,
        connectedPortItemsAndAdjacentRealNode: _tp.Sequence[_mfs.PortItemAndAdjacentRealNode],
    ) -> _mfn.RealNodeBase:
        raise NotImplementedError()
