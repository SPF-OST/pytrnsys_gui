import typing as _tp

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QLineF
from PyQt5.QtWidgets import QGraphicsLineItem

from trnsysGUI.SegmentItemBase import SegmentItemBase  # type: ignore[attr-defined]

# This is needed to avoid a circular import but still be able to type check
if _tp.TYPE_CHECKING:
    from trnsysGUI.Connection import Connection  # type: ignore[attr-defined]  #  pylint: disable=unused-import


class DoublePipeSegmentItem(SegmentItemBase):
    def __init__(self, startNode, endNode, parent: "Connection"):
        super().__init__(startNode, endNode, parent)

        self.blueLine = QGraphicsLineItem(self)
        self.redLine = QGraphicsLineItem(self)

    def _createSegment(self, startNode, endNode) -> "SegmentItemBase":
        return DoublePipeSegmentItem(startNode, endNode, self.connection)

    def _setLineImpl(self, x1, y1, x2, y2):
        self.blueLine.setPen(QtGui.QPen(QtCore.Qt.blue, 3))
        self.redLine.setPen(QtGui.QPen(QtCore.Qt.red, 3))
        offset = 3

        if abs(y1 - y2) < 1:
            self.blueLine.setLine(x1, y1 + offset, x2, y2 + offset)
            self.redLine.setLine(x1, y1 - offset, x2, y2 - offset)
        elif abs(x1 - x2) < 1:
            self.blueLine.setLine(x1 + offset, y1, x2 + offset, y2)
            self.redLine.setLine(x1 - offset, y1, x2 - offset, y2)
        else:
            # Initially, connections go directly between its two ports: only
            # afterwards are they broken up into horizontal and vertical segments.
            # This is probably an artifact of back when connections didn't have to
            # be straight. Once, these artifacts have been removed, we should throw here.
            pass
        self.linePoints = QLineF(x1, y1, x2, y2)

    def updateGrad(self):
        self.blueLine.setPen(QtGui.QPen(QtCore.Qt.blue, 3))
        self.redLine.setPen(QtGui.QPen(QtCore.Qt.red, 3))

    def setSelect(self, isSelected: bool) -> None:
        if isSelected:
            selectPen = self._createSelectPen()
            self.blueLine.setPen(selectPen)
            self.redLine.setPen(selectPen)
        else:
            self.updateGrad()

    def setColorAndWidthAccordingToMassflow(self, color, width):
        pass
