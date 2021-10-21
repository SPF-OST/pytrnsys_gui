# pylint: skip-file
# type: ignore

from math import sqrt
import typing as tp

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QLineF
from PyQt5.QtWidgets import QGraphicsLineItem

from trnsysGUI.SegmentItemBase import SegmentItemBase

# This is needed to avoid a circular import but still be able to type check
if tp.TYPE_CHECKING:
    from trnsysGUI.Connection import Connection


class DoublePipeSegmentItem(SegmentItemBase):
    def __init__(self, startNode, endNode, parent: "Connection"):
        super().__init__(startNode, endNode, parent)

        self.blueLine = QGraphicsLineItem(self)
        self.redLine = QGraphicsLineItem(self)

    def setLine(self, *args):
        super().setLine(*args)
        self.blueLine.setPen(QtGui.QPen(QtCore.Qt.blue, 3))
        self.redLine.setPen(QtGui.QPen(QtCore.Qt.red, 3))
        offset = 3

        if abs(self.y1 - self.y2) < 1:
            self.blueLine.setLine(self.x1, self.y1 + offset, self.x2, self.y2 + offset)
            self.redLine.setLine(self.x1, self.y1 - offset, self.x2, self.y2 - offset)
        else:
            self.blueLine.setLine(self.x1 + offset, self.y1, self.x2 + offset, self.y2)
            self.redLine.setLine(self.x1 - offset, self.y1, self.x2 - offset, self.y2)
        self.linePoints = QLineF(self.x1, self.y1, self.x2, self.y2)

    def updateGrad(self):
        """
        Updates the gradient by calling the interpolation function
        Returns
        -------

        """

        self.blueLine.setPen(QtGui.QPen(QtCore.Qt.blue, 3))
        self.redLine.setPen(QtGui.QPen(QtCore.Qt.red, 3))

    def setHighlight(self, isHighlight: bool) -> None:
        if isHighlight:
            highlightPen = self._createHighlightPen()
            self.blueLine.setPen(highlightPen)
            self.redLine.setPen(highlightPen)
        else:
            self.updateGrad()