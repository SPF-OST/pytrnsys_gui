import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.sourceSinkBase import SourceSinkBase


class Source(SourceSinkBase):
    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SOURCE_SVG
