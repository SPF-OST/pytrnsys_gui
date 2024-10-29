# pylint: skip-file

import typing as _tp

import trnsysGUI.BlockItem as _bi
import trnsysGUI.blockItemGraphicItemMixins as _bimx
import trnsysGUI.images as _img


class PV(_bi.BlockItem, _bimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        _bi.BlockItem.__init__(self, trnsysType, editor, displayName)
        _bimx.SvgBlockItemGraphicItemMixin.__init__(self)

        self.w = 100
        self.h = 100

        self.changeSize()

    @classmethod
    @_tp.override
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.PV_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40
        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)
        return w, h
