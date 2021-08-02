# pylint: skip-file
# type: ignore

import random

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QGraphicsItemGroup, QGraphicsLineItem, QMenu

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
        name
    ):
        super().__init__(parent)
        self.parent = parent
        self.logger = parent.logger

        self._lines = []
        self.w = width

        self.sSide = sideNr
        self.id = self.parent.parent.parent().idGen.getID()
        self.trnsysId = self.parent.parent.parent().idGen.getTrnsysID()

        self.parent.heatExchangers.append(self)
        self.setZValue(100)

        self.port1 = PortItem("i", self.sSide, self.parent)
        self.port2 = PortItem("o", self.sSide, self.parent)

        self.parent.inputs.append(self.port1)
        self.parent.outputs.append(self.port2)

        self._setRelativeHeightsAndTankSize(
            storageTankWidth,
            storageTankHeight,
            relativeInputHeight,
            relativeOutputHeight,
        )

        self.displayName = name
        
        self._draw()

    def _draw(self):
        self.port1.setZValue(100)
        self.port2.setZValue(100)

        randomValue = int(random.uniform(20, 200))
        randomColor = QColor(randomValue, randomValue, randomValue)
        self.port1.innerCircle.setBrush(randomColor)
        self.port2.innerCircle.setBrush(randomColor)
        self.port1.visibleColor = randomColor
        self.port2.visibleColor = randomColor

        self._drawCoils()

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

    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction("Rename...")
        a1.triggered.connect(self.renameHx)

        menu.exec_(event.screenPos())

    def mousePressEvent(self, event):
        self.highlightHx()
        self.logger.debug("pressed")

    def renameHx(self):
        # dia = hxDlg(self, self.scene().parent())
        self.scene().parent().showHxDlg(self)

    def rename(self, newName):
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

    def setTankSize(self, storageTankWidth, storageTankHeight):
        self._clearDrawing()

        self._setRelativeHeightsAndTankSize(
            storageTankWidth,
            storageTankHeight,
            self.relativeInputHeight,
            self.relativeOutputHeight,
        )

        self._drawCoils()

    def setRelativeHeights(self, relativeInputHeight: float, relativeOutputHeight: float) -> None:
        self._clearDrawing()

        self._setRelativeHeightsAndTankSize(
            self._storageTankWidth,
            self._storageTankHeight,
            relativeInputHeight,
            relativeOutputHeight,
        )

        self._drawCoils()

    def _drawCoils(self):
        sign = 1 if self.sSide == 0 else -1

        x, y = self._getPos()
        lineTop = QGraphicsLineItem(
            x - sign * self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS,
            y + 0,
            x + sign * self.w,
            y + 0,
            self,
        )
        lineTop.setPen(QPen(Qt.black, 2))
        self._lines.append(lineTop)
        times = self.h / self.COIL_HEIGHT_IN_PIXELS
        self.logger.debug("Times is " + str(times))
        for i in range(int(times)):
            line1 = QGraphicsLineItem(
                x + sign * self.w,
                y + i * self.COIL_HEIGHT_IN_PIXELS,
                x + sign * (1 - self.COIL_WITH_RELATIVE_TO_TANK_WIDTH) * self.w,
                y + (i + 1 / 2) * self.COIL_HEIGHT_IN_PIXELS,
                self,
            )

            line2 = QGraphicsLineItem(
                x + sign * (1 - self.COIL_WITH_RELATIVE_TO_TANK_WIDTH) * self.w,
                y + (i + 1 / 2) * self.COIL_HEIGHT_IN_PIXELS,
                x + sign * self.w,
                y + (i + 1) * self.COIL_HEIGHT_IN_PIXELS,
                self,
            )

            line1.setPen(QPen(Qt.black, 2))
            line2.setPen(QPen(Qt.black, 2))

            self._lines.append(line1)
            self._lines.append(line2)
        lineBottom = QGraphicsLineItem(
            x - sign * self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS,
            y + self.h,
            x + sign * self.w,
            y + self.h,
            self,
        )
        lineBottom.setPen(QPen(Qt.black, 2))
        self._lines.append(lineBottom)

    def _clearDrawing(self):
        for line in self._lines:
            self.parent.parent.parent().diagramScene.removeItem(line)

        self._lines = []

    def _setRelativeHeightsAndTankSize(
        self,
        storageTankWidth,
        storageTankHeight,
        relativeInputHeight,
        relativeOutputHeight,
    ):
        self._storageTankWidth = storageTankWidth
        self._storageTankHeight = storageTankHeight

        self.relativeOutputHeight = relativeOutputHeight
        self.relativeInputHeight = relativeInputHeight

        relativeHeight = relativeInputHeight - relativeOutputHeight
        absoluteHeight = relativeHeight * storageTankHeight

        self.h = absoluteHeight - absoluteHeight % self.COIL_HEIGHT_IN_PIXELS

        self._setPortPositions()

    def _setPortPositions(self):
        x, y = self._getPos()
        sign = 1 if self.sSide == 0 else -1
        xWithProtrusion = x - sign * self.PORT_ITEM_PROTRUSION_SIZE_IN_PIXELS
        self.port1.setPos(xWithProtrusion, y)
        self.port2.setPos(xWithProtrusion, y + self.h)

    def _getPos(self):
        x = 0 if self.sSide == 0 else self._storageTankWidth
        y = self._storageTankHeight - self.relativeInputHeight * self._storageTankHeight
        return x, y


