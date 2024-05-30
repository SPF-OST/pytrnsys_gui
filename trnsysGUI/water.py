import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.sourceSinkBase import SourceSinkBase


class Water(SourceSinkBase):
    def _getImageAccessor(self) -> _img.SvgImageAccessor:
        return _img.WATER_SVG
