from PyQt5 import QtCore
from PyQt5.QtCore import QRectF, QSize, QPointF
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
            # print("relative pos has changed")
            self.parent.setItemSize(self.pos().x(), self.pos().y())
            self.parent.updateImage()
            return QPointF(value.x(), value.x())

        return super(ResizerItem, self).itemChange(change, value)

    # def mouseReleaseEvent(self, event):
    #     self.setPos(self.parent.boundingRect().bottomRight())
    #     super(ResizerItem, self).mouseReleaseEvent(event)
    #
    # def dragMoveEvent(self, event):
    #     self.setPos(event.pos().x(), event.pos().x())
    #     print("sdfhs")
    #     super(ResizerItem, self).dragMoveEvent(event)