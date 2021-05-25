import random

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsLineItem, QMenu

from trnsysGUI.Connection import Connection
from trnsysGUI.PortItem import PortItem


class HeatExchanger(QGraphicsItemGroup):
    COIL_HEIGHT_IN_PIXELS = 10
    COIL_WITH_RELATIVE_TO_TANK_WIDTH = 0.6
    PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS = 8

    def __init__(
        self,
        sideNr,
        width,
        relativeInputHeight,
        relativeOutputHeight,
        storageTankWidth,
        storageTankHeight,
        parent,
        name="Untitled",
        **kwargs
    ):
        super(HeatExchanger, self).__init__(parent)
        self.parent = parent
        self.logger = parent.logger
        xOffset = 0 if sideNr == 0 else storageTankWidth
        yOffset = storageTankHeight - relativeInputHeight * storageTankHeight
        self.offset = QPointF(xOffset, yOffset)
        self._lines = []
        self.w = width

        self.relativeOutputHeight = relativeOutputHeight
        self.relativeInputHeight = relativeInputHeight

        relativeHeight = relativeInputHeight - relativeOutputHeight
        self.h = relativeHeight * storageTankHeight
        self.sSide = sideNr
        self.id = self.parent.parent.parent().idGen.getID()

        self.conn = None

        self.parent.heatExchangers.append(self)
        self.setZValue(100)

        self.port1 = PortItem("i", self.sSide, self.parent)
        self.port2 = PortItem("o", self.sSide, self.parent)

        self.port1.isFromHx = True
        self.port2.isFromHx = True

        self.parent.inputs.append(self.port1)
        self.parent.outputs.append(self.port2)

        if self.sSide == 0:
            self.port1.setPos(
                self.offset + QPointF(-self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS, 0)
            )
            self.port2.setPos(
                self.offset
                + QPointF(0, self.h)
                + QPointF(-self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS, 0)
            )
        if self.sSide == 2:
            self.port1.setPos(
                self.offset + QPointF(self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS, 0)
            )
            self.port2.setPos(
                self.offset
                + QPointF(0, self.h)
                + QPointF(self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS, 0)
            )

        if kwargs == {} or "tempHx" in kwargs:
            self.logger.debug("Creating new HeatExchanger")
            if kwargs == {}:
                self.displayName = name + str(self.id)
            elif "tempHx" in kwargs:
                self.displayName = name
            self.initNew()
            self.loadedConnTrId = None  # Should not be used
        else:
            if "loadedHx" in kwargs:
                self.logger.debug("Loading existing HeatExchanger")
                self.displayName = name
                self.loadedConnTrId = kwargs["connTrnsysID"]

    def initNew(self):
        self.conn = Connection(
            self.port1, self.port2, True, self.parent.parent.parent()
        )
        self.conn.displayName = self.displayName

        self.port1.setZValue(100)
        self.port2.setZValue(100)

        randomValue = int(random.uniform(20, 200))
        self.port1.innerCircle.setBrush(QColor(randomValue, randomValue, randomValue))
        self.port2.innerCircle.setBrush(QColor(randomValue, randomValue, randomValue))
        self.port1.visibleColor = QColor(randomValue, randomValue, randomValue)
        self.port2.visibleColor = QColor(randomValue, randomValue, randomValue)

        self.draw()

    def initLoad(self):
        self.logger.debug("Finishing up HeatExchanger loading")
        self.logger.debug("self port1 is " + str(self.port1))
        self.logger.debug("self port2  is " + str(self.port2))

        self.conn = Connection(
            self.port1, self.port2, True, self.parent.parent.parent()
        )
        self.conn.displayName = self.displayName
        self.conn.trnsysId = self.loadedConnTrId

        self.port1.setZValue(100)
        self.port2.setZValue(100)

        randomValue = int(random.uniform(20, 200))
        self.port1.innerCircle.setBrush(QColor(randomValue, randomValue, randomValue))
        self.port2.innerCircle.setBrush(QColor(randomValue, randomValue, randomValue))
        self.port1.visibleColor = QColor(randomValue, randomValue, randomValue)
        self.port2.visibleColor = QColor(randomValue, randomValue, randomValue)

        # StartPos is a QPoint
        self.draw()

    def setId(self, newId):
        self.id = newId

    def setParent(self, p):
        self.parent = p

        if p.name is "StorageTank":
            self.logger.debug("p is a StorageTank")
            self.setParentItem(p)
        else:
            self.logger.debug(
                "A non-Storage-Tank block is trying to set parent of heatExchanger"
            )

    def draw(self):
        sign = 1 if self.sSide == 0 else -1

        o = self.offset
        self.floorHeight()
        lineTop = QGraphicsLineItem(
            o.x() - sign * self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS,
            o.y() + 0,
            o.x() + sign * self.w,
            o.y() + 0,
            self,
        )
        lineTop.setPen(QPen(Qt.black, 2))
        self._lines.append(lineTop)
        times = self.h / self.COIL_HEIGHT_IN_PIXELS
        self.logger.debug("Times is " + str(times))
        for i in range(int(times)):
            line1 = QGraphicsLineItem(
                o.x() + sign * self.w,
                o.y() + i * self.COIL_HEIGHT_IN_PIXELS,
                o.x() + sign * (1 - self.COIL_WITH_RELATIVE_TO_TANK_WIDTH) * self.w,
                o.y() + (i + 1 / 2) * self.COIL_HEIGHT_IN_PIXELS,
                self,
            )

            line2 = QGraphicsLineItem(
                o.x() + sign * (1 - self.COIL_WITH_RELATIVE_TO_TANK_WIDTH) * self.w,
                o.y() + (i + 1 / 2) * self.COIL_HEIGHT_IN_PIXELS,
                o.x() + sign * self.w,
                o.y() + (i + 1) * self.COIL_HEIGHT_IN_PIXELS,
                self,
            )

            line1.setPen(QPen(Qt.black, 2))
            line2.setPen(QPen(Qt.black, 2))

            self._lines.append(line1)
            self._lines.append(line2)
        lineBottom = QGraphicsLineItem(
            o.x() - sign * self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS,
            o.y() + self.h,
            o.x() + sign * self.w,
            o.y() + self.h,
            self,
        )
        lineBottom.setPen(QPen(Qt.black, 2))
        self._lines.append(lineBottom)

    def floorHeight(self):
        self.h = self.h - self.h % self.COIL_HEIGHT_IN_PIXELS
        self.port2.pos().setY(self.h)

    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction("Rename...")
        a1.triggered.connect(self.renameHx)

        a2 = menu.addAction("PLACEHOLDER TO FILL THIS EMPTY SPACE (Delete...)")

        a3 = menu.addAction("PLACEHOLDER TO FILL THIS EMPTY SPACE (Change position)")

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

    def redraw(self):
        self._clearDrawing()
        self.h = self.port2.pos().y() - self.port1.pos().y()

        if self.sSide == 0:
            self.offset = QPointF(0, self.port1.pos().y())
        else:
            self.offset = QPointF(self.parent.w, self.port1.pos().y())

        self.draw()

    def _clearDrawing(self):
        for line in self._lines:
            self.parent.parent.parent().diagramScene.removeItem(line)

        self._lines = []

    def mousePressEvent(self, event):
        self.highlightHx()
        self.logger.debug("pressed")

    def modifyPosition(self, newHeights):
        relativeInputHeight = (
            newHeights[0] / 100 if newHeights[0] != "" else self.relativeInputHeight
        )
        relativeOutputHeight = (
            newHeights[1] / 100 if newHeights[1] != "" else self.relativeOutputHeight
        )

        self.relativeInputHeight = relativeInputHeight
        self.relativeOutputHeight = relativeOutputHeight

        self.h = self.parent.h * (relativeInputHeight - relativeOutputHeight)

        xOffset = 0 if self.sSide == 0 else self.parent.w
        adjustedXOffset = (
            xOffset - self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS
            if self.sSide == 0
            else xOffset + self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS
        )
        yOffset = self.parent.h - relativeInputHeight * self.parent.h

        self.offset = QPointF(xOffset, yOffset)

        self.port1.setPos(adjustedXOffset, yOffset)
        self.port2.setPos(adjustedXOffset, yOffset + self.h)

        self._clearDrawing()
        self.draw()
