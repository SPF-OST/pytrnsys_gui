from PyQt5 import QtCore
from PyQt5.QtCore import QRectF, QSize
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem


class ResizerItem(QGraphicsEllipseItem):
    def __init__(self, parent):
        QGraphicsEllipseItem.__init__(self, QRectF(-8, -8, 16.0, 16.0), parent)
        self.parent = parent
        self.setPos(self.parent.w, self.parent.h)
        self.setBrush(QBrush(QtCore.Qt.black))
        p1 = QPen(QColor(0,0,0))
        self.setPen(p1)
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)

    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            print("relative pos has changed")
            self.parent.setItemSize(self.pos().x(), self.pos().y())
            self.parent.updatePixmap()

        return super(ResizerItem, self).itemChange(change, value)