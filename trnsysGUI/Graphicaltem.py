from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QImage, QCursor, QIcon
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QGraphicsPixmapItem

from trnsysGUI.ResizerItem import ResizerItem


class GraphicalItem(QGraphicsPixmapItem):

    def __init__(self, parent):

        super(GraphicalItem, self).__init__(None)
        self.w = 100.0
        self.h = 100.0
        self.parent = parent
        # self.image = QImage("images/genericItem")
        # self.image = QImage("gear.svg")
        self.image = QPixmap(QIcon("gear.svg").pixmap(QSize(self.w, self.h)).toImage())
        self.setPixmap(self.image)

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.resizer = ResizerItem(self)

    def setItemSize(self, w, h):
        self.w, self.h = w, h

    def updatePixmap(self):
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))
