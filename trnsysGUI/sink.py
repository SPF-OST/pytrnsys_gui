import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.sourceSinkBase import SourceSinkBase


class Sink(SourceSinkBase):
    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SINK_SVG
