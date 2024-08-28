# pylint: disable = invalid-name

from __future__ import annotations

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.internalPiping as _ip
import trnsysGUI.sideNrs as _snrs

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.connectionBase as _cb


class PortItemBase(_qtw.QGraphicsEllipseItem):  # pylint: disable = too-many-instance-attributes
    def __init__(self, name, parent):
        self.parent = parent

        self.logger = parent.logger

        self.name = name
        self.createdAtSide = None
        self.posCallbacks = []
        self.connectionList: list[_cb.ConnectionBase] = []
        self.id = self.parent.editor.idGen.getID()  # pylint: disable = invalid-name

        self.color = "white"
        self.ashColorR = _qtg.QColor(239, 57, 75)
        self.ashColorB = _qtg.QColor(20, 83, 245)

        super().__init__(-4, -4, 7.0, 7.0, parent)

        self.innerCircle = _qtw.QGraphicsEllipseItem(-4, -4, 6, 6, self)
        self.innerCircle.setPen(_qtg.QPen(_qtg.QColor(0, 0, 0, 0), 0))

        self.visibleColor = _qtg.QColor(0, 0, 0)

        self.innerCircle.setBrush(self.visibleColor)

        self.setCursor(_qtg.QCursor(_qtc.Qt.CrossCursor))
        # self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        # The Port itself is larger than only the innerCircle
        self.setBrush(_qtg.QBrush(_qtc.Qt.white))

        # Hacky fix for no border of ellipse
        p1 = _qtg.QPen(_qtg.QColor(0, 0, 0, 0), 0)  # pylint: disable = invalid-name
        self.setPen(p1)

        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)

        # QUndo framework related
        self.savePos = None
        self.savedPos = False

    def setParent(self, p):  # pylint: disable = invalid-name
        self.parent = p
        self.setParentItem(p)

    @property
    def side(self) -> _snrs.SideNr:
        blockItem = self.parent

        transform = blockItem.transform()

        blockItemRect = _qtc.QRect(0, 0, blockItem.w, blockItem.h)
        mappedBlockItemRect = transform.mapRect(blockItemRect)

        portItemRect = self.rect()
        portItemRectInParentCoordinates = self.mapRectToParent(portItemRect)
        mappedPortItemRect = transform.mapRect(portItemRectInParentCoordinates)

        sideNr = _snrs.getSideNr(mappedPortItemRect, mappedBlockItemRect)

        return sideNr

    def itemChange(self, change, value):
        # pylint: disable = fixme, too-many-branches, too-many-statements, too-many-nested-blocks
        # TODO : here to merge segments when moving blockitems
        if (
            self.parent.editor.moveDirectPorts
            and hasattr(self.parent, "heatExchangers")
            and change == self.ItemPositionChange
        ):
            if not self.savePos is None:
                self.logger.debug("val is " + str(value))
                value.setY(max(value.y(), 0))
                value.setY(min(value.y(), self.parent.h))

                return _qtc.QPointF(self.savePos.x(), value.y())

        if change != self.ItemScenePositionHasChanged:
            return super().itemChange(change, value)

        for conn in self.connectionList:
            if conn.fromPort is self:
                if (self.createdAtSide not in (1, 3)) or not conn.segments[0].isVertical():
                    if len(conn.getCorners()) > 0 and len(conn.segments) > 0:
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
                                    self.hideCorners(conn)
                                    verSeg.setVisible(False)
                                else:
                                    self.showCorners(conn)
                                    verSeg.setVisible(True)
                else:
                    if len(conn.getCorners()) > 0 and len(conn.segments) > 0:
                        cor = conn.getCorners()[0]
                        cor.setPos(self.scenePos().x(), cor.pos().y())

                        seg = conn.segments[0]  # first segment
                        seg.setLine(self.scenePos().x(), self.scenePos().y(), cor.scenePos().x(), cor.scenePos().y())

            elif conn.toPort is self:
                if (conn.fromPort.createdAtSide not in (1, 3)) or not conn.segments[0].isVertical():
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
                                    self.hideCorners(conn)
                                    verSeg.setVisible(False)
                                else:
                                    self.showCorners(conn)
                                    verSeg.setVisible(True)
                else:
                    if len(conn.getCorners()) == 1 and len(conn.segments) > 0:
                        cor = conn.getCorners()[-1]
                        cor.setPos(cor.pos().x(), self.scenePos().y())

                        seg = conn.segments[-1]  # last segment
                        seg.setLine(self.scenePos().x(), self.scenePos().y(), cor.scenePos().x(), cor.scenePos().y())
                    elif len(conn.getCorners()) == 2 and len(conn.segments) > 0:
                        cor = conn.getCorners()[-1]
                        cor.setPos(self.scenePos().x(), cor.pos().y())

                        seg = conn.segments[-1]  # last segment
                        seg.setLine(self.scenePos().x(), self.scenePos().y(), cor.scenePos().x(), cor.scenePos().y())

            else:
                raise ValueError("moving a portItem, portItem is neither from nor toPort")

        for posCallback in self.posCallbacks:  # pylint: disable = invalid-name
            posCallback(value)

        return value

    def mousePressEvent(self, event):  # pylint: disable = unused-argument
        if self.parent.editor.moveDirectPorts and hasattr(self.parent, "heatExchangers"):
            self.setFlag(self.ItemIsMovable)
            self.savePos = self.pos()
            return

        if self.connectionList:
            return

        self.setFlag(self.ItemIsMovable, False)
        self.parent.editor.startConnection(self)

    def hoverEnterEvent(self, event):  # pylint: disable = unused-argument
        self.logger.debug(self.parent)

        self.enlargePortSize()

        self.innerCircle.setBrush(self.ashColorB)

        self._highlightInternallyConnectedPortItems()

        self.debugprint()

    def enlargePortSize(self):
        if not self.savedPos:
            self.setPos(self.pos().x() - 3, self.pos().y() - 3)
            self.savedPos = True
        self.setRect(-4, -4, 10, 10)
        self.innerCircle.setRect(-4, -4, 10, 10)

    def hoverLeaveEvent(self, event):  # pylint: disable = unused-argument
        self.resetPortSize()

        self.innerCircle.setBrush(self.visibleColor)

        self._unhighlightInternallyConnectedPortItems()

        self._debugClear()

    def resetPortSize(self):
        if self.savedPos:
            self.setPos(self.pos().x() + 3, self.pos().y() + 3)
            self.savedPos = False
        self.setRect(-4, -4, 7, 7)
        self.innerCircle.setRect(-4, -4, 6.5, 6.5)

    def debugprint(self):

        self.parent.editor.contextInfoList.addItem("ID: " + str(self.id))

        formattedPortItems = self._getFormattedPortItems()
        jointFormattedPortItems = "\n".join(formattedPortItems)
        self.parent.editor.contextInfoList.addItem(f"Names: {jointFormattedPortItems}")

        self.parent.editor.contextInfoList.addItem("Block: " + self.parent.displayName)

        self.parent.editor.contextInfoList.addItem("Connections:")
        for connection in self.connectionList:
            self.parent.editor.contextInfoList.addItem(connection.displayName)

    def _getFormattedPortItems(self) -> _tp.Sequence[str]:
        internalPiping: _ip.InternalPiping = self.parent.getInternalPiping()

        portItems = internalPiping.getModelPortItems(self)

        formattedPortItems = []
        for portItem in portItems:
            node = internalPiping.getNode(self, portItem.type)
            nodeNameOrEmpty = node.name or ""

            formattedPortItem = f"{nodeNameOrEmpty}{portItem.name} ({portItem.direction.value})"

            formattedPortItems.append(formattedPortItem)

        return formattedPortItems

    def _debugClear(self):
        self.parent.editor.contextInfoList.clear()

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

    def _getConnectedMassFlowContributor(
        self, massFlowContributor: _ip.HasInternalPiping
    ) -> _tp.Optional[_ip.HasInternalPiping]:
        if massFlowContributor == self.parent:
            return self.getConnectionOrNone()

        connection = self.getConnectionOrNone()

        if not connection or connection != massFlowContributor:
            raise ValueError("`massFlowContributor' is not adjacent to this port item.")

        return self.parent

    def isConnected(self) -> bool:
        return bool(self.connectionList)

    def getConnectionOrNone(self) -> _tp.Optional[_cb.ConnectionBase]:
        if not self.connectionList:
            return None

        assert len(self.connectionList) == 1

        connection = self.connectionList[0]

        return connection

    def getConnection(self) -> _cb.ConnectionBase:
        assert self.isConnected()

        connection = self.getConnectionOrNone()
        assert connection  # for mypy

        return connection

    def _highlightInternallyConnectedPortItems(self):
        raise NotImplementedError()

    def _unhighlightInternallyConnectedPortItems(self):
        raise NotImplementedError()
