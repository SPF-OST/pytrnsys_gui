import typing as _tp

from PyQt5 import QtGui as _qtg
from PyQt5 import QtWidgets as _qtw

import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.imageAccessor as _ia


class SvgBlockItem(_bip.BlockItemHasInternalPiping):
    @_tp.override
    def _getImageAccessor(self) -> _tp.Optional[_ia.SvgImageAccessor]:
        raise NotImplementedError()

    def paint(self, painter: _qtg.QPainter, option: _qtw.QStyleOptionGraphicsItem, widget: _qtw.QWidget) -> None:
        imageAccessor = self._getImageAccessor()
        renderer = imageAccessor.createRenderer()

        bounds = self.boundingRect()
        renderer.render(painter, bounds)
