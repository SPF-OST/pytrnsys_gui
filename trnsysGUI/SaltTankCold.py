# pylint: skip-file

import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.SaltTankBase import SaltTankBase


class SaltTankCold(SaltTankBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SALT_TANK_COLD_SVG
