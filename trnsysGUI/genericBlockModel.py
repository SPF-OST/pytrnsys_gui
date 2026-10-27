import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import trnsysGUI.blockItemModel as _bim
import trnsysGUI.serialization as _gser


@_dc.dataclass
class GenericBlockModel(
    _gser.BlockItemUpgradableJsonSchemaMixinVersion0,
    _gser.RequiredDecoderFieldsMixin,
):
    blockItemModel: _bim.BlockItemBaseModel
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    # Side of each port pair (same index as `portsIdsIn` and `portsIdsOut`), in the coordinates
    # of the block (i.e. before flipping and rotating)
    portPairSides: _tp.List[int]
    imageResourcePath: str

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("e190d093-f226-4d1a-bcb6-3024e6c1a925")
