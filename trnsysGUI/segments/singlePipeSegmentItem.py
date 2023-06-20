from __future__ import annotations

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw
from PyQt5.QtGui import QColor

import trnsysGUI.cornerItem as _ci
import trnsysGUI.segments.segmentItemBase as _sib

from . import _common


_LINE_PEN_WIDTH = 4

# This is needed to avoid a circular import but still be able to type check
if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc


class SinglePipeSegmentItem(_sib.SegmentItemBase):  # type: ignore[name-defined]
    def __init__(self, startNode, endNode, parent: _spc.SinglePipeConnection):
        super().__init__(startNode, endNode, parent)

        self._singlePipeConnection = parent

        self.singleLine = _qtw.QGraphicsLineItem(self)
        self.initGrad()

    def _createSegment(self, startNode, endNode) -> _sib.SegmentItemBase:  # type: ignore[name-defined]
        return SinglePipeSegmentItem(startNode, endNode, self._singlePipeConnection)

    def _getContextMenu(self) -> _qtw.QMenu:
        menu = super()._getContextMenu()

        editHydraulicLoopAction = menu.addAction("Edit hydraulic loop")

        editHydraulicLoopAction.triggered.connect(self._singlePipeConnection.editHydraulicLoop)

        return menu

    def _setLineImpl(self, x1, y1, x2, y2):
        self.initGrad()
        self.singleLine.setLine(x1, y1, x2, y2)
        self.linePoints = self.singleLine.line()

    def initGrad(self) -> None:
        gradient = self._createGradient()
        self._updateLine(gradient)

    def _createGradient(self) -> _qtg.QGradient:
        if isinstance(self.startNode.parent, _ci.CornerItem):  # type: ignore[attr-defined]
            startBlock = self.startNode.firstNode().parent
        else:
            startBlock = self.startNode.parent
        if isinstance(self.endNode.parent, _ci.CornerItem):  # type: ignore[attr-defined]
            endBlock = self.endNode.lastNode().parent
        else:
            endBlock = self.endNode.parent
        gradient = _qtg.QLinearGradient(
            _qtc.QPointF(startBlock.fromPort.scenePos().x(), startBlock.fromPort.scenePos().y()),
            _qtc.QPointF(endBlock.toPort.scenePos().x(), endBlock.toPort.scenePos().y()),
        )
        gradient.setColorAt(0, _qtc.Qt.gray)
        gradient.setColorAt(1, _qtc.Qt.black)
        return gradient

    def _setStandardLinesPens(self) -> None:
        gradient = self._createUpdatedGradient()
        self._updateLine(gradient)

    def _createUpdatedGradient(self) -> _qtg.QGradient:
        totLenConn = self.connection.totalLength()
        partLen1 = self.connection.partialLength(self.startNode)
        partLen2 = self.connection.partialLength(self.endNode)
        if isinstance(self.startNode.parent, _ci.CornerItem):  # type: ignore[attr-defined]
            startGradP = _qtc.QPointF(self.startNode.parent.scenePos().x(), self.startNode.parent.scenePos().y())
        elif self.startNode.prevN() is None:
            startGradP = _qtc.QPointF(
                self.startNode.parent.fromPort.scenePos().x(), self.startNode.parent.fromPort.scenePos().y()
            )
        else:
            startGradP = _qtc.QPointF(self.line().p1().x(), self.line().p1().y())
        if isinstance(self.endNode.parent, _ci.CornerItem):  # type: ignore[attr-defined]
            endGradP = _qtc.QPointF(self.endNode.parent.scenePos().x(), self.endNode.parent.scenePos().y())
        elif self.endNode.nextN() is None:
            endGradP = _qtc.QPointF(
                self.endNode.parent.toPort.scenePos().x(), self.endNode.parent.toPort.scenePos().y()
            )
        else:
            endGradP = _qtc.QPointF(self.line().p2().x(), self.line().p2().y())
        gradient = _qtg.QLinearGradient(startGradP, endGradP)
        gradient.setColorAt(0, self._interpolate(partLen1, totLenConn))
        gradient.setColorAt(1, self._interpolate(partLen2, totLenConn))
        return gradient

    def _interpolate(
        self,
        segmentLength: int,
        connectionLength: int,
    ) -> _qtg.QColor:
        alpha = 255 if self._singlePipeConnection.shallBeSimulated else _common.NOT_SIMULATED_COLOR_ALPHA

        red1 = 160
        blue1 = 160
        green1 = 160

        red2 = 0
        blue2 = 0
        green2 = 0

        try:
            factor1 = int(segmentLength / connectionLength)
            factor2 = int((connectionLength - segmentLength) / connectionLength)
        except ZeroDivisionError:
            return QColor(100, 100, 100, alpha)
        else:
            return QColor(
                factor1 * red2 + factor2 * red1,
                factor1 * green2 + factor2 * green1,
                factor1 * blue2 + factor2 * blue1,
                alpha,
            )

    def _updateLine(self, gradient: _qtg.QGradient) -> None:
        pen = self._createPen(gradient)
        self.singleLine.setPen(pen)

    def _createPen(self, gradient: _qtg.QGradient) -> _qtg.QPen:
        brush = _qtg.QBrush(gradient)
        pen = _qtg.QPen(brush, _LINE_PEN_WIDTH)

        if self._singlePipeConnection.shallBeSimulated:
            return pen

        pen.setStyle(_qtc.Qt.DashLine)
        return pen

    def _setSelectedLinesPen(self):
        selectPen = self._createSelectedLinesPen()
        self.singleLine.setPen(selectPen)

    def setColorAndWidthAccordingToMassflow(self, color, width):
        pen1 = _qtg.QPen(color, width)
        self.singleLine.setPen(pen1)
