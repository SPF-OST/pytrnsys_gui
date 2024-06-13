import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.imageAccessor as _ia


class BlockItemGraphicItemMixinBase:
    @classmethod
    def _getImageAccessor(cls) -> _ia.ImageAccessorBase:
        raise NotImplementedError()

    def boundingRect(self) -> _qtc.QRectF:
        raise NotImplementedError()

    def paint(
        self,
        painter: _qtg.QPainter,
        option: _qtw.QStyleOptionGraphicsItem,  # pylint: disable=unused-argument
        widget: _qtw.QWidget | None = None,  # pylint: disable=unused-argument
    ) -> None:
        raise NotImplementedError()


class SvgBlockItemGraphicItemMixin(BlockItemGraphicItemMixinBase):
    @_tp.override
    def _getImageAccessor(self) -> _ia.SvgImageAccessor:
        raise NotImplementedError()

    @_tp.override
    def boundingRect(self) -> _qtc.QRectF:
        raise NotImplementedError()

    @_tp.override
    def paint(
        self,
        painter: _qtg.QPainter,
        option: _qtw.QStyleOptionGraphicsItem,  # pylint: disable=unused-argument
        widget: _qtw.QWidget | None = None,  # pylint: disable=unused-argument
    ) -> None:
        imageAccessor = self._getImageAccessor()
        bounds = self.boundingRect()
        imageAccessor.renderer.render(painter, bounds)


class RasterImageBlockItemMixin(BlockItemGraphicItemMixinBase):
    def __init__(self):
        imageAccessor = self._getImageAccessor()
        self._image = imageAccessor.image()

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _ia.ImageAccessorBase:
        raise NotImplementedError()

    @_tp.override
    def boundingRect(self) -> _qtc.QRectF:
        raise NotImplementedError()

    @_tp.override
    def paint(
        self,
        painter: _qtg.QPainter,
        option: _qtw.QStyleOptionGraphicsItem,  # pylint: disable=unused-argument
        widget: _qtw.QWidget | None = None,  # pylint: disable=unused-argument
    ) -> None:
        painter.drawImage(self.boundingRect(), self._image)
