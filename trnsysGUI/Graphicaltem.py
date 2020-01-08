from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap, QImage, QCursor
from PyQt5.QtWidgets import QGraphicsPixmapItem

from trnsysGUI.ResizerItem import ResizerItem


class GraphicalItem(QGraphicsPixmapItem):

    def __init__(self, parent):

        super(GraphicalItem, self).__init__(None)
        self.w = 100.0
        self.h = 100.0
        self.parent = parent
        self.image = QImage("images/genericItem")
        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(self.w, self.h))

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.resizer = ResizerItem(self)


