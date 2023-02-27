# pylint: skip-file

import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.SaltTankBase import SaltTankBase


class SaltTankHot(SaltTankBase):
    def __init__(self, trnsysType, editor, **kwargs):
        super(SaltTankHot, self).__init__(trnsysType, editor, **kwargs)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SALT_TANK_HOT_SVG
