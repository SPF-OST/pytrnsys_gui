from PyQt5 import QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QImage, QCursor, QIcon
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QGraphicsPixmapItem, QMenu, QFileDialog

from trnsysGUI.ResizerItem import ResizerItem


class GraphicalItem(QGraphicsPixmapItem):

    def __init__(self, parent):

        super(GraphicalItem, self).__init__(None)
        self.w = 100.0
        self.h = 100.0
        self.parent = parent
        # self.image = QImage("images/genericItem")
        # self.image = QImage("gear.svg")

        # Initial icon
        self.imageSource = "gear.svg"
        self.image = QPixmap(QIcon(self.imageSource).pixmap(QSize(self.w, self.h)).toImage())
        self.setPixmap(self.image)

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.resizer = ResizerItem(self)

    def setItemSize(self, w, h):
        self.w, self.h = w, h

    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction("Load different image")
        a1.triggered.connect(self.loadAction)

        menu.exec_(event.screenPos())

    def loadAction(self):
        fileName = QFileDialog.getOpenFileName(self.parent.parent(), "Load image", filter="*.svg")[0]
        if fileName != "":
            self.setImageSource(fileName)
            self.updateImage()

    def setImageSource(self, s):
        self.imageSource = s

    def updateImage(self):
        self.image = QPixmap(QIcon(self.imageSource).pixmap(QSize(self.w, self.h)).toImage())
        self.setPixmap(self.image)

