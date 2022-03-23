# pylint: skip-file
# type: ignore

from PyQt5 import QtCore
from PyQt5.QtCore import QRectF, QSize, QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem


class ResizerItem(QGraphicsEllipseItem):
    def __init__(self, parent):
        QGraphicsEllipseItem.__init__(self, QRectF(-4, -4, 8, 8), parent)
        self.parent = parent
        self.setPos(self.parent.w, self.parent.h)
        self.setBrush(Qt.transparent)
        p1 = QPen()
        p1.setStyle(Qt.DotLine)
        self.setPen(p1)
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)

    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            self.parent.setItemSize(self.pos().x(), self.pos().y())
            self.parent.updateImage()
            return QPointF(value.x(), value.x())

        return super(ResizerItem, self).itemChange(change, value)

    def delete(self):
        del self
