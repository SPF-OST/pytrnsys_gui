import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.serialization as _gser


@_dc.dataclass
class TVentilModelVersion1(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable = invalid-name
    BlockDisplayName: str  # pylint: disable = invalid-name
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable = invalid-name
    trnsysId: int
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return _bim.BlockItemModelVersion1

    @classmethod
    def upgrade(cls, superseded: _bim.BlockItemModelVersion1) -> "TVentilModelVersion1":  # type: ignore[override]
        assert len(superseded.portsIdsIn) == 2
        assert len(superseded.portsIdsOut) == 1

        inputPortIds = [superseded.portsIdsOut[0]]
        outputPortIds = [superseded.portsIdsIn[0], superseded.portsIdsIn[1]]

        return TVentilModelVersion1(
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.blockPosition,
            superseded.Id,
            superseded.trnsysId,
            inputPortIds,
            outputPortIds,
            superseded.flippedH,
            superseded.flippedV,
            superseded.rotationN,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("3fff9a8a-d40e-42e2-824d-c015116d0a1d")

    @classmethod
    @_tp.override
    def additionalProperties(cls) -> bool:
        return True


@_dc.dataclass
class ValveModel(_gser.BlockItemUpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin):
    blockItemModel: _bim.BlockItemBaseModel
    inputPortId: int
    outputPortIds: _tp.Tuple[int, int]

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return TVentilModelVersion1

    @classmethod
    def upgrade(cls, superseded: _bim.BlockItemModelVersion1) -> "ValveModel":  # type: ignore[override]
        assert isinstance(superseded, TVentilModelVersion1)

        assert len(superseded.portsIdsIn) == 1
        assert len(superseded.portsIdsOut) == 2

        inputPortId = superseded.portsIdsIn[0]
        outputPortIds = (superseded.portsIdsOut[0], superseded.portsIdsOut[1])

        blockItemModel = _bim.createBlockItemBaseModelFromLegacyModel(superseded)

        return ValveModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            blockItemModel,
            inputPortId,
            outputPortIds,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("ccf7f590-c65e-4fa1-bf7c-1850a5f8985e")

    @classmethod
    def additionalProperties(cls) -> bool:
        return True
