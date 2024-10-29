import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.sourceSinkBase import SourceSinkBase


class Sink(SourceSinkBase):
    @classmethod
    @_tp.override
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.SINK_SVG

    @classmethod
    def _getInputAndOutputXPos(cls) -> tuple[int, int]:
        return (40, 20)
