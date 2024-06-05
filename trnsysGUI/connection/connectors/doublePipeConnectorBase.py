import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.serialization as _gser
import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip


class DoublePipeConnectorBase(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.w = 40
        self.h = 20

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.editor.idGen.getTrnsysID())

    def getDisplayName(self) -> str:
        return self.displayName

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return False

    @classmethod
    @_tp.override
    def shallRenameOutputTemperaturesInHydraulicFile(cls) -> bool:
        return False

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        raise NotImplementedError()

    def rotateBlockCW(self):
        super().rotateBlockCW()
        self._flipPipes()

    def rotateBlockCCW(self):
        super().rotateBlockCCW()
        self._flipPipes()

    def resetRotation(self):
        super().resetRotation()
        self.updateFlipStateV(0)

    def encode(self) -> _tp.Tuple[str, _dcj.JsonDict]:
        blockItemModel = self._encodeBaseModel()

        inputPortIds = [p.id for p in self.inputs]
        outputPortIds = [p.id for p in self.outputs]

        connectorModel = DoublePipeBlockItemModel(
            self.name, self.displayName, blockItemModel, inputPortIds, outputPortIds, self.childIds
        )

        dictName = "Block-"
        return dictName, connectorModel.to_dict()

    def decode(self, i, resBlockList) -> None:
        model = DoublePipeBlockItemModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)

        blockItemModel = model.blockItemModel

        self.setPos(float(blockItemModel.blockPosition[0]), float(blockItemModel.blockPosition[1]))
        self.trnsysId = blockItemModel.trnsysId
        self.childIds = model.childIds

        for index, inp in enumerate(self.inputs):
            inp.id = model.inputPortIds[index]

        for index, out in enumerate(self.outputs):
            out.id = model.outputPortIds[index]

        self.updateFlipStateH(blockItemModel.flippedH)
        self.updateFlipStateV(blockItemModel.flippedV)
        self.rotateBlockToN(blockItemModel.rotationN)

        resBlockList.append(self)

    def getInternalPiping(self) -> _ip.InternalPiping:
        raise NotImplementedError()

    def _flipPipes(self):
        angle = (self.rotationN % 4) * 90
        if angle == 0:
            self.updateFlipStateV(False)
        elif angle == 90:
            self.updateFlipStateV(True)
        elif angle == 180:
            self.updateFlipStateV(True)
        elif angle == 270:
            self.updateFlipStateV(False)


@_dc.dataclass
class DoublePipeBlockItemModelVersion0(
    _ser.UpgradableJsonSchemaMixinVersion0
):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable=invalid-name
    BlockDisplayName: str  # pylint: disable=invalid-name
    blockPosition: _tp.Tuple[float, float]
    id: int  # pylint: disable=invalid-name
    trnsysId: int
    childIds: _tp.List[int]
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("e5149c30-9f05-4a3a-8a3c-9ada74143802")


@_dc.dataclass
class DoublePipeBlockItemModel(_ser.UpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin):
    blockItemModel: _bim.BlockItemBaseModel
    inputPortIds: _tp.List[int]
    outputPortIds: _tp.List[int]
    childIds: _tp.List[int]

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,  # pylint: disable=duplicate-code
        validate_enums: bool = True,  # /NOSONAR
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> "DoublePipeBlockItemModel":
        data.pop(".__BlockDict__")
        doublePipeBlockItemModel = super().from_dict(data, validate, validate_enums, schema_type)
        return _tp.cast(DoublePipeBlockItemModel, doublePipeBlockItemModel)

    def to_dict(
        self,
        omit_none: bool = True,  # /NOSONAR
        validate: bool = False,
        validate_enums: bool = True,  # /NOSONAR
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums, schema_type)  # pylint: disable=duplicate-code
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return DoublePipeBlockItemModelVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "DoublePipeBlockItemModel":
        if not isinstance(superseded, DoublePipeBlockItemModelVersion0):
            raise ValueError(f"`superseded` is not of type {DoublePipeBlockItemModelVersion0.__name__}")

        blockItemModel = _bim.createBlockItemBaseModelFromLegacyModel(superseded)

        return DoublePipeBlockItemModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            blockItemModel,
            superseded.portsIdsIn,
            superseded.portsIdsOut,
            superseded.childIds,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("0c739f73-abed-4d1b-b7ec-1c81e04791cd")
