from __future__ import annotations

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.segments.segmentItemBase as _sib
import trnsysGUI.dialogs.connections.doublePipe as _dpcldlg

from trnsysGUI.segments import _common

_LINE_PEN_WIDTH = 3

# This is needed to avoid a circular import but still be able to type check
if _tp.TYPE_CHECKING:  # pragma: no cover
    import trnsysGUI.connection.doublePipeConnection as _dpc


class DoublePipeSegmentItem(_sib.SegmentItemBase):  # type: ignore[name-defined]
    def __init__(self, startNode, endNode, parent: _dpc.DoublePipeConnection):
        super().__init__(startNode, endNode, parent)

        self.blueLine = _qtw.QGraphicsLineItem(self)
        self.redLine = _qtw.QGraphicsLineItem(self)

    @property
    def _doublePipeConnection(self) -> _dpc.DoublePipeConnection:
        return _tp.cast("_dpc.DoublePipeConnection", self.connection)

    def _getContextMenu(self) -> _qtw.QMenu:
        menu = super()._getContextMenu()
        action = menu.addAction("Edit properties...")
        action.triggered.connect(self._editProperties)

        return menu

    def _editProperties(self):
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
        self._doublePipeConnection.shallBeSimulated = (
            connection.shallBeSimulated
        )

        self._doublePipeConnection.updateSegmentGradients()

    def _setLineImpl(self, x1, y1, x2, y2):
        self.resetLinePens()

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
            # be straight. Once these artifacts have been removed, we should throw here.
            pass
        self.linePoints = _qtc.QLineF(x1, y1, x2, y2)

    def _setStandardLinesPens(self) -> None:
        bluePen = self._createPen(_qtc.Qt.blue)
        self.blueLine.setPen(bluePen)
        redPen = self._createPen(_qtc.Qt.red)
        self.redLine.setPen(redPen)

    def _createPen(self, globalColor: _qtc.Qt.GlobalColor) -> _qtg.QPen:
        if self._doublePipeConnection.shallBeSimulated:
            return _qtg.QPen(globalColor, _LINE_PEN_WIDTH)

        color = self._getTransparentColor(
            globalColor, _common.NOT_SIMULATED_COLOR_ALPHA
        )
        pen = _qtg.QPen(color, _LINE_PEN_WIDTH)
        pen.setStyle(_qtc.Qt.DashLine)

        return pen

    @staticmethod
    def _getTransparentColor(
        globalColor: _qtc.Qt.GlobalColor, alpha: int
    ) -> _qtg.QColor:
        color = _qtg.QColor(globalColor)
        color.setAlpha(alpha)
        return color

    def _setSelectedLinesPen(self):
        selectPen = self._createSelectedLinesPen()
        self.blueLine.setPen(selectPen)
        self.redLine.setPen(selectPen)

    def setColorAndWidthAccordingToMassflow(self, color, width):
        # No need to do anything here
        pass
