# pylint: skip-file

import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.SaltTankBase import SaltTankBase


class SaltTankHot(SaltTankBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

    @classmethod
    @_tp.override
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.SALT_TANK_HOT_SVG
