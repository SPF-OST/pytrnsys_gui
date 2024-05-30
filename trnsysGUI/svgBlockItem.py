import typing as _tp

from PyQt5 import QtGui as _qtg
from PyQt5 import QtWidgets as _qtw

import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.imageAccessor as _ia


class SvgBlockItem(_bip.BlockItemHasInternalPiping):
    @_tp.override
    def _getImageAccessor(self) -> _ia.SvgImageAccessor:
        raise NotImplementedError()

    @_tp.override
    def paint(
        self,
        painter: _qtg.QPainter,
        option: _qtw.QStyleOptionGraphicsItem,  # pylint: disable=unused-argument
        widget: _qtw.QWidget | None = None,  # pylint: disable=unused-argument
    ) -> None:
        imageAccessor = self._getImageAccessor()
        renderer = imageAccessor.createRenderer()

        bounds = self.boundingRect()
        renderer.render(painter, bounds)
