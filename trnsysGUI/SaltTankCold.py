# pylint: skip-file
# type: ignore

import typing as _tp

import trnsysGUI.images as _img
from trnsysGUI.SaltTank import SaltTank

class SaltTankCold(SaltTank):

    def __init__(self, trnsysType, parent, **kwargs):
        super(SaltTankCold, self).__init__(trnsysType, parent, **kwargs)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SALT_TANK_COLD_SVG