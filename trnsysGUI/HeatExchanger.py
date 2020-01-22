import random

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsLineItem, QMenu, QGraphicsRectItem

from trnsysGUI.PortItem import PortItem
# from trnsysGUI.StorageTank import StorageTank
from trnsysGUI.hxDlg import hxDlg
from trnsysGUI.Connection import Connection


class HeatExchanger(QGraphicsItemGroup):
    partH = 20

    def __init__(self, side, sizeW, sizeH, offset, parent, name='Untitled', **kwargs):
        super(HeatExchanger, self).__init__(parent)
        self.parent = parent
        self.offset = offset  # QPointF
        self.lines = []
        self.w = sizeW
        self.h = sizeH
        self.sSide = side
        self.id = self.parent.parent.parent().idGen.getID()

        # self.rectangle = QGraphicsRectItem(0,0 ,self.w -5, self.h, self)

        self.conn = None

        self.parent.heatExchangers.append(self)
        self.setZValue(100)

        self.port1 = PortItem('i', self.sSide, self.parent)
        self.port2 = PortItem('o', self.sSide, self.parent)

        self.port1.isFromHx = True
        self.port2.isFromHx = True

        self.parent.inputs.append(self.port1)
        self.parent.outputs.append(self.port2)

        delta = 4
        if self.sSide == 0:
            self.port1.setPos(self.offset + QPointF(-2 * delta, 0))
            self.port2.setPos(self.offset + QPointF(0, self.h) + QPointF(-2 * delta, 0))
        if self.sSide == 2:
            self.port1.setPos(self.offset + QPointF(2 * delta, 0))
            self.port2.setPos(self.offset + QPointF(0, self.h) + QPointF(2 * delta, 0))

        if kwargs == {}:
            print("Creating new HeatExchanger")
            self.displayName = name + str(self.id)
            self.initNew()
            self.loadedConnTrId = None  # Should not be used
        else:
            if "loadedHx" in kwargs:
                print("Loading existing HeatExchanger")
                self.displayName = name
                self.loadedConnTrId = kwargs["connTrnsysID"]

    def initNew(self):

        self.conn = Connection(self.port1, self.port2, True, self.parent.parent.parent())
        self.conn.displayName = self.displayName

        self.port1.setZValue(100)
        self.port2.setZValue(100)

        randomValue = int(random.uniform(20, 200))
        self.port1.outerRing.setBrush(QColor(randomValue, randomValue, randomValue))
        self.port2.outerRing.setBrush(QColor(randomValue, randomValue, randomValue))
        self.port1.visibleColor = QColor(randomValue, randomValue, randomValue)
        self.port2.visibleColor = QColor(randomValue, randomValue, randomValue)

        # StartPos is a QPoint
        self.drawHx(6, 0.4)

    def initLoad(self):
        print("Finishing up HeatExchanger loading")
        print("self port1 is " + str(self.port1))
        print("self port2  is " + str(self.port2))

        self.conn = Connection(self.port1, self.port2, True, self.parent.parent.parent())
        self.conn.displayName = self.displayName
        self.conn.trnsysId = self.loadedConnTrId

        self.port1.setZValue(100)
        self.port2.setZValue(100)

        randomValue = int(random.uniform(20, 200))
        self.port1.outerRing.setBrush(QColor(randomValue, randomValue, randomValue))
        self.port2.outerRing.setBrush(QColor(randomValue, randomValue, randomValue))
        self.port1.visibleColor = QColor(randomValue, randomValue, randomValue)
        self.port2.visibleColor = QColor(randomValue, randomValue, randomValue)

        # StartPos is a QPoint
        self.drawHx(6, 0.4)

    def setId(self, newId):
        self.id = newId

    def setParent(self, p):
        self.parent = p

        if p.name is "StorageTank":
            print("p is a StorageTank")
            self.setParentItem(p)
        else:
            print("A non-Storage-Tank block is trying to set parent of heatExchanger")

    def drawHx(self, param, factor):
        if self.sSide == 0:
            self.drawHxL(param, factor)

        if self.sSide == 2:
            self.drawHxR(param, factor)

    def drawHxL(self, param, factor):
        # self.offset is the height of the first port
        s = self.offset
        delta = 4
        # set bb = True for equal amount of lines
        bb = False
        if bb:
            lineTop = QGraphicsLineItem(s.x() - 2 * delta, s.y() + 0, s.x() + self.w, s.y() + 0, self)
            lineTop.setPen(QPen(Qt.black, 2))
            self.lines.append(lineTop)

            sw = 0
            for i in range(param):
                line = QGraphicsLineItem(s.x() + self.w - factor * (sw % 2) * self.w, s.y() + i * self.h / param,
                                         s.x() + self.w - factor * ((sw + 1) % 2) * self.w,
                                         s.y() + (i + 1) * self.h / param, self)
                line.setPen(QPen(Qt.black, 2))
                self.lines.append(line)
                sw = (sw + 1)

            lineBottom = QGraphicsLineItem(s.x() - 2 * delta, s.y() + self.h, s.x() + self.w,
                                           s.y() + self.h,
                                           self)
            lineBottom.setPen(QPen(Qt.black, 2))
            self.lines.append(lineBottom)
        else:
            self.floorHeight()
            lineTop = QGraphicsLineItem(s.x() - 2 * delta, s.y() + 0, s.x() + self.w, s.y() + 0, self)
            lineTop.setPen(QPen(Qt.black, 2))
            self.lines.append(lineTop)

            times = self.h / HeatExchanger.partH
            param = times / 2
            print("Times is " + str(times))

            for i in range(int(times)):
                # line = QGraphicsLineItem(s.x() + self.w - factor * (sw % 2) * self.w, s.y() + i * self.h / param,
                #                          s.x() + self.w - factor * ((sw + 1) % 2) * self.w,
                #                          s.y() + (i + 1) * self.h / param, self)

                line1 = QGraphicsLineItem(s.x() + self.w, s.y() + i * HeatExchanger.partH,
                                          s.x() + self.w - factor * self.w, s.y() + (i + 1 / 2) * HeatExchanger.partH,
                                          self)
                line2 = QGraphicsLineItem(s.x() + self.w - factor * self.w, s.y() + (i + 1 / 2) * HeatExchanger.partH,
                                          s.x() + self.w, s.y() + (i + 1) * HeatExchanger.partH, self)

                line1.setPen(QPen(Qt.black, 2))
                line2.setPen(QPen(Qt.black, 2))
                self.lines.append(line1)
                self.lines.append(line2)

            lineBottom = QGraphicsLineItem(s.x() - 2 * delta, s.y() + self.h, s.x() + self.w,
                                           s.y() + self.h,
                                           self)
            lineBottom.setPen(QPen(Qt.black, 2))
            self.lines.append(lineBottom)

            # self.rectangle.setPos(lineTop.line().p1().x(), lineTop.line().p1().y())

    def drawHxR(self, param, factor):
        s = self.offset
        delta = 4
        # set bb = True for equal amount of line segments between the ports

        bb = False
        if bb:
            lineTop = QGraphicsLineItem(s.x() + 2 * delta, s.y() + 0, s.x() - self.w, s.y() + 0, self)
            lineTop.setPen(QPen(Qt.black, 2))
            self.lines.append(lineTop)

            sw = 0
            for i in range(param):
                line = QGraphicsLineItem(s.x() - self.w + (1 - factor) * (sw % 2) * self.w, s.y() + i * self.h / param,
                                         s.x() - self.w + (1 - factor) * ((sw + 1) % 2) * self.w,
                                         s.y() + (i + 1) * self.h / param, self)
                line.setPen(QPen(Qt.black, 2))
                self.lines.append(line)
                sw = (sw + 1)

            lineBottom = QGraphicsLineItem(s.x() + 2 * delta, s.y() + self.h, s.x() - self.w,
                                           s.y() + self.h,
                                           self)
            lineBottom.setPen(QPen(Qt.black, 2))
            self.lines.append(lineBottom)

        else:
            self.floorHeight()
            lineTop = QGraphicsLineItem(s.x() + 2 * delta, s.y() + 0, s.x() - self.w, s.y() + 0, self)
            lineTop.setPen(QPen(Qt.black, 2))
            self.lines.append(lineTop)

            times = self.h / HeatExchanger.partH
            param = times / 2
            print("Times is " + str(times))

            for i in range(int(times)):
                # line = QGraphicsLineItem(s.x() + self.w - factor * (sw % 2) * self.w, s.y() + i * self.h / param,
                #                          s.x() + self.w - factor * ((sw + 1) % 2) * self.w,
                #                          s.y() + (i + 1) * self.h / param, self)

                line1 = QGraphicsLineItem(s.x() - self.w, s.y() + i * HeatExchanger.partH,
                                          s.x() - self.w + (1 - factor) * self.w,
                                          s.y() + (i + 1 / 2) * HeatExchanger.partH,
                                          self)
                line2 = QGraphicsLineItem(s.x() - self.w + (1 - factor) * self.w,
                                          s.y() + (i + 1 / 2) * HeatExchanger.partH,
                                          s.x() - self.w, s.y() + (i + 1) * HeatExchanger.partH, self)

                line1.setPen(QPen(Qt.black, 2))
                line2.setPen(QPen(Qt.black, 2))
                self.lines.append(line1)
                self.lines.append(line2)

            lineBottom = QGraphicsLineItem(s.x() + 2 * delta, s.y() + self.h, s.x() - self.w,
                                           s.y() + self.h,
                                           self)
            lineBottom.setPen(QPen(Qt.black, 2))
            self.lines.append(lineBottom)

            # self.rectangle.setPos(lineTop.line().p2().x(), lineTop.line().p2().y())

    def floorHeight(self):
        delta = 4
        # Could be used if static partH would be used for the heatexchanger
        self.h = self.h - self.h % HeatExchanger.partH
        if self.sSide == 0:
            self.port2.setPos(self.offset + QPointF(0, self.h) + QPointF(-2 * delta, 0))
        if self.sSide == 2:
            self.port2.setPos(self.offset + QPointF(0, self.h) + QPointF(2 * delta, 0))

    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction('Rename...')
        a1.triggered.connect(self.renameHx)

        a2 = menu.addAction('PLACEHOLDER TO FILL THIS EMPTY SPACE (Delete...)')

        a3 = menu.addAction('PLACEHOLDER TO FILL THIS EMPTY SPACE (Change position)')

        menu.exec_(event.screenPos())

    def renameHx(self):
        # dia = hxDlg(self, self.scene().parent())
        self.scene().parent().showHxDlg(self)

    def rename(self, newName):
        self.conn.displayName = newName
        self.displayName = newName

    def highlightHx(self):
        for ch in self.childItems():
            if isinstance(ch, QGraphicsLineItem):
                pen1 = QPen(QColor(125, 242, 189), 3)
                ch.setPen(pen1)

    def unhighlightHx(self):
        for ch in self.childItems():
            if isinstance(ch, QGraphicsLineItem):
                ch.setPen(QPen(Qt.black, 2))

    def updateLines(self, h):
        self.removeLines()

        self.h = self.port2.pos().y() - self.port1.pos().y()

        if self.sSide == 0:
            self.offset = QPointF(0, self.port1.pos().y())
        else:
            self.offset = QPointF(self.parent.w, self.port1.pos().y())

        self.drawHx(6, 0.4)

    def removeLines(self):
        while len(self.lines) != 0:
            self.parent.parent.parent().diagramScene.removeItem(self.lines[0])
            self.lines.remove(self.lines[0])

    def mousePressEvent(self, event):
        self.highlightHx()
        print("pressed")
        # super(HeatExchanger, self).keyPressEvent(event)