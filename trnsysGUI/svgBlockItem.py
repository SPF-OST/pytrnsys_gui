import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
from PyQt5 import QtWidgets as _qtw

import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.imageAccessor as _ia


class SvgBlockItem(_bip.BlockItemHasInternalPiping):
    @_tp.override
    def _getImageAccessor(self) -> _ia.SvgImageAccessor:
        raise NotImplementedError()

    @_tp.override
    def updateFlipStateH(self, state: bool) -> None:
        self.flippedH = bool(state)
        self._updateTransform()

    @_tp.override
    def updateFlipStateV(self, state: bool) -> None:
        self.flippedV = bool(state)
        self._updateTransform()

    @_tp.override
    def _rotateBlock(self, nQuarterTurns: int) -> None:
        self.rotationN = nQuarterTurns

        self.label.setRotation(-self.rotationN * 90)

        self._updateTransform()

        nQuarterTurnsNeeded = nQuarterTurns - self.rotationN
        for p in self.inputs:
            p.itemChange(_qtw.QGraphicsItem.ItemScenePositionHasChanged, p.scenePos())
            self.updateSide(p, nQuarterTurnsNeeded)
        for p1 in self.outputs:
            p1.itemChange(_qtw.QGraphicsItem.ItemScenePositionHasChanged, p1.scenePos())
            self.updateSide(p1, nQuarterTurnsNeeded)

    def _updateTransform(self) -> None:
        scaleX = -1 if self.flippedH else 1
        scaleY = -1 if self.flippedV else 1
        scale = _qtg.QTransform.fromScale(scaleX, scaleY)

        translateX = self.h if self.flippedH else 0
        translateY = self.w if self.flippedV else 0
        translate = _qtg.QTransform.fromTranslate(translateX, translateY)

        angle = self.rotationN * 90
        rotate = _qtg.QTransform().rotate(angle)

        transform = scale * translate * rotate

        self.setTransform(transform)

    @_tp.override
    def paint(
        self,
        painter: _qtg.QPainter,
        option: _qtw.QStyleOptionGraphicsItem,  # pylint: disable=unused-argument
        widget: _qtw.QWidget | None = None,  # pylint: disable=unused-argument
    ) -> None:
        imageAccessor = self._getImageAccessor()
        bounds = _qtc.QRectF(0, 0, self.w, self.h)
        imageAccessor.renderer.render(painter, bounds)
