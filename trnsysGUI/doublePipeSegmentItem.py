import typing as _tp

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QLineF
from PyQt5.QtWidgets import QGraphicsLineItem, QMenu

from trnsysGUI.SegmentItemBase import SegmentItemBase  # type: ignore[attr-defined]
import trnsysGUI.dialogs.connectionDialogs.doublePipeConnectionLengthDialog as _dpcldlg

# This is needed to avoid a circular import but still be able to type check
from trnsysGUI.dialogs.connectionDialogs.doublePipeConnectionLengthDialog import LengthContainer

if _tp.TYPE_CHECKING:
    from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection
    # type: ignore[attr-defined]  #  pylint: disable=unused-import


class DoublePipeSegmentItem(SegmentItemBase):
    def __init__(self, startNode, endNode, parent: "DoublePipeConnection"):
        super().__init__(startNode, endNode, parent)

        self._doublePipeConnection = parent
        self.blueLine = QGraphicsLineItem(self)
        self.redLine = QGraphicsLineItem(self)
        self.lengthContainer = None

    def _createSegment(self, startNode, endNode) -> "SegmentItemBase":
        return DoublePipeSegmentItem(startNode, endNode, self.connection)

    def _getContextMenu(self) -> QMenu:
        self.lengthContainer = self._doublePipeConnection.lengthContainer
        menu = super()._getContextMenu()
        action = menu.addAction("Provide length")
        action.triggered.connect(self.editLength)
        self._doublePipeConnection.lengthInM = self.lengthContainer.lengthInM

        return menu

    def editLength(self):
        _dpcldlg.doublePipeConnectionLengthDialog(self.lengthContainer)

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
