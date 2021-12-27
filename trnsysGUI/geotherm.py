import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.sourceSinkBase import SourceSinkBase


class Geotherm(SourceSinkBase):
    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.GEOTHERM_SVG
