import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.sourceSinkBase import SourceSinkBase


class Water(SourceSinkBase):
    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.WATER_SVG
