from __future__ import annotations

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.SegmentItemBase as _sib
import trnsysGUI.dialogs.connections.doublePipe as _dpcldlg

# This is needed to avoid a circular import but still be able to type check
if _tp.TYPE_CHECKING:
    from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection

    # type: ignore[attr-defined]  #  pylint: disable=unused-import


class DoublePipeSegmentItem(_sib.SegmentItemBase):  # type: ignore[name-defined]
    def __init__(self, startNode, endNode, parent: DoublePipeConnection):
        super().__init__(startNode, endNode, parent)

        self.blueLine = _qtw.QGraphicsLineItem(self)
        self.redLine = _qtw.QGraphicsLineItem(self)

    @property
    def _doublePipeConnection(self) -> DoublePipeConnection:
        return self.connection

    def _createSegment(self, startNode, endNode) -> _sib.SegmentItemBase:  # type: ignore[name-defined]
        return DoublePipeSegmentItem(startNode, endNode, self._doublePipeConnection)

    def _getContextMenu(self) -> _qtw.QMenu:
        menu = super()._getContextMenu()
        action = menu.addAction("Edit properties...")
        action.triggered.connect(self._editLength)

        return menu

    def _editLength(self):
        connection = _dpcldlg.ConnectionModel(
            self._doublePipeConnection.displayName,
            self._doublePipeConnection.lengthInM,
            self._doublePipeConnection.shallBeSimulated,
        )

        dialog = _dpcldlg.DoublePipeConnectionPropertiesDialog(connection)
        dialogCode = dialog.exec()

        if dialogCode != _qtw.QDialog.Accepted:
            return

        self._doublePipeConnection.lengthInM = connection.lengthInM
        self._doublePipeConnection.shallBeSimulated = connection.shallBeSimulated

    def _setLineImpl(self, x1, y1, x2, y2):
        self.blueLine.setPen(_qtg.QPen(_qtc.Qt.blue, 3))
        self.redLine.setPen(_qtg.QPen(_qtc.Qt.red, 3))
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
        self.linePoints = _qtc.QLineF(x1, y1, x2, y2)

    def updateGrad(self):
        self.blueLine.setPen(_qtg.QPen(_qtc.Qt.blue, 3))
        self.redLine.setPen(_qtg.QPen(_qtc.Qt.red, 3))

    def setSelect(self, isSelected: bool) -> None:
        if isSelected:
            selectPen = self._createSelectPen()
            self.blueLine.setPen(selectPen)
            self.redLine.setPen(selectPen)
        else:
            self.updateGrad()

    def setColorAndWidthAccordingToMassflow(self, color, width):
        pass
