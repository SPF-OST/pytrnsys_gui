from PyQt5 import QtCore
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QBrush, QCursor, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem

# from trnsysGUI.test import getID


class PortItem(QGraphicsEllipseItem):
    def __init__(self, name, side, parent):
        self.parent = parent
        self.name = name
        self.side = side
        self.posCallbacks = []
        self.connectionList = []
        self.id = self.parent.parent.parent().idGen.getID()
        # This boolean is used when the storage inside is connected, thus preventing Hx to connect to that.
        self.isFromHx = False

        # For debugging connections at StorageTank
        self.visited = False

        # For saving the connection of a port pair in a Tank
        self.portPairVisited = False

        self.color = 'white'
        self.ashColorR = QColor(239, 57, 75)
        self.ashColorB = QColor(20, 83, 245)

        QGraphicsEllipseItem.__init__(self, QRectF(-8, -8, 16.0, 16.0), parent)
        # QGraphicsEllipseItem.__init__(self, QRectF(-7, -7, 14.0, 14.0), parent)
        self.outerRing = QGraphicsEllipseItem(-4, -4, 8, 8, self)
        self.outerRing.setPen(QPen(QColor(0, 0, 0, 0), 0))

        if name == 'i':
            color = QColor(self.ashColorR)
            # self.outerRing.setBrush(QColor(self.ashColorR))
            self.outerRing.setBrush(QColor(0, 0, 0))

        if name == 'o':
            color = QColor(self.ashColorB)
            # self.outerRing.setBrush(QColor(self.ashColorB))
            self.outerRing.setBrush(QColor(0, 0, 0))

        self.setCursor(QCursor(QtCore.Qt.CrossCursor))
        # self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        # self.setBrush(QBrush(color))
        self.setBrush(QBrush(QtCore.Qt.white))

        # Hacky fix for no border of ellipse
        p1 = QPen(QColor(0, 0, 0, 0), 0)
        self.setPen(p1)

        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setAcceptHoverEvents(True)

    def setParent(self, p):
        self.parent = p
        self.setParentItem(p)

    def itemChange(self, change, value):

        # Here is something strange going on:
        # posCallback is filled from unknown line
        # The following lines are strange:
        # print(str(self.scene()))    # Prints object of type diagramScene, ok
        # print(str(self.scene().items))  # Error that NoneType object has no attribute 'items'
        # Sometimes scene is None!

        if change == self.ItemScenePositionHasChanged and self.parent.parent.parent().editorMode == 0:
            for conn in self.connectionList:
                conn.positionLabel()

                if conn.fromPort is self:
                    # print("This port is the starting port of connection")
                    # nextNodeInConn = conn.startNode.nextN()
                    # print("Type of parent is " + str(type(nextNodeInConn.parent)))

                    e = conn.segments[0]
                    e.setLine(self.scenePos().x(), self.scenePos().y(), e.line().p2().x(),
                              e.line().p2().y())



                if conn.toPort is self:
                    # print("This port is the ending port of connection")
                    # nextNodeInConn = conn.endNode.prevN()
                    # print("nextnodeinconn is " + str(conn.endNode.prevN()))
                    # print("nextNode is " + str(nextNodeInConn))
                    # print("Type of parent is " + str(type(nextNodeInConn.parent)))

                    # New
                    e = conn.segments[-1]
                    e.setLine(e.line().p1().x(), e.line().p1().y(), self.scenePos().x(), self.scenePos().y())



                # global pasting
                if not self.parent.parent.parent().pasting:
                    for s in conn.segments:
                        s.updateGrad()

        if change == self.ItemScenePositionHasChanged and self.parent.parent.parent().editorMode == 1:
            for conn in self.connectionList:
                conn.positionLabel()

                if conn.fromPort is self:
                    if len(conn.getCorners()) > 0 and len(conn.segments) > 0:
                        cor = conn.getCorners()[0]
                        cor.setPos(cor.pos().x(), self.scenePos().y())

                        seg = conn.segments[0]
                        seg.setLine(self.scenePos().x(), self.scenePos().y(), cor.scenePos().x(), cor.scenePos().y())
                elif conn.toPort is self:
                    if len(conn.getCorners()) > 0 and len(conn.segments) > 0:
                        cor = conn.getCorners()[-1]
                        cor.setPos(cor.pos().x(), self.scenePos().y())

                        seg = conn.segments[-1]
                        seg.setLine(self.scenePos().x(), self.scenePos().y(), cor.scenePos().x(), cor.scenePos().y())
                else:
                    print("Error: In Mode 1, moving a portItem, portItem is wether from nor toPort")

        # These line are somehow needed, need to investigate why
        if change == self.ItemScenePositionHasChanged:
            # print(str(change))
            for cb in self.posCallbacks:
                cb(value)
            return value
        return super(PortItem, self).itemChange(change, value)

    def mousePressEvent(self, event):
        self.scene().parent().startConnection(self)

    def hoverEnterEvent(self, event):
        # print("Hovering")

        self.setRect(-7, -7, 14.0, 14.0)
        self.outerRing.setRect(-7, -7, 14.0, 14.0)
        if self.name == 'i':
            # self.setBrush(Qt.red)
            # self.outerRing.setBrush(Qt.red)
            self.outerRing.setBrush(QColor(0,0,0))
        if self.name == 'o':
            # self.setBrush(QColor(Qt.blue))
            # self.outerRing.setBrush(QColor(Qt.blue))
            self.outerRing.setBrush(QColor(0,0,0))


    def hoverLeaveEvent(self, event):
        # print("Leaving hover")

        # self.setRect(-6, -6, 12, 12)
        self.setRect(-7, -7, 14, 14)
        self.outerRing.setRect(-4, -4, 8, 8)
        if len(self.connectionList) == 0:
            if self.name == 'i':
                # self.setBrush(Qt.red)
                # self.setBrush(self.ashColorR)
                # self.outerRing.setBrush(self.ashColorR)
                self.outerRing.setBrush(QColor(0, 0, 0))

            if self.name == 'o':
                # self.setBrush(self.ashColorR)
                # self.outerRing.setBrush(self.ashColorB)
                self.outerRing.setBrush(QColor(0, 0, 0))

