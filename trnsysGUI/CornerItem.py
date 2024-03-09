import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

from trnsysGUI.segments.Node import Node


class CornerItem(_qtw.QGraphicsEllipseItem):
    def __init__(self, x, y, r1, r2, prevNode, nextNode, parent):
        super().__init__(x, y, r1, r2, parent=parent)

        self.logger = parent.logger

        self.parent = parent
        self.setBrush(_qtg.QBrush(_qtc.Qt.black))
        self.node = Node(self, prevNode, nextNode)
