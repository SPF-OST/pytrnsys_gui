import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import pytrnsys.utils.serialization as _ser
import trnsysGUI.blockItemModel as _bim


@_dc.dataclass
class TeePieceBaseModel(_ser.UpgradableJsonSchemaMixinVersion0):
    blockItemModel: _bim.BlockItemBaseModel
    inputPortId: int
    outputPortIds: _tp.Tuple[int, int]

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("260c8083-5343-4345-8cb3-0cdd374bc076")


class TeePieceLegacyModelProtocol(
    _bim.BlockItemLegacyModelProtocol, _tp.Protocol
):
    portsIdsIn: list[int]
    portsIdsOut: list[int]


def createTeePieceBaseModelFromLegacyModel(
    superseded: TeePieceLegacyModelProtocol,
) -> TeePieceBaseModel:
    blockItemModel = _bim.createBlockItemBaseModelFromLegacyModel(superseded)

    assert len(superseded.portsIdsIn) == 1
    inputPortId = superseded.portsIdsIn[0]

    assert len(superseded.portsIdsOut) == 2
    outputPortIds = (superseded.portsIdsOut[0], superseded.portsIdsOut[1])

    baseModel = TeePieceBaseModel(
        blockItemModel,
        inputPortId,
        outputPortIds,
    )

    return baseModel
