import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.serialization as _gser
import trnsysGUI.teePieces.exportHelper as _eh
import trnsysGUI.teePieces.teePieceBase as _tpb
import trnsysGUI.teePieces.teePieceBaseModel as _tpbm


class TeePiece(_tpb.TeePieceBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self._setModels()

        self.changeSize()

    def _createInputAndOutputPorts(self) -> _tp.Tuple[_pib.PortItemBase, _pib.PortItemBase, _pib.PortItemBase]:
        return (
            _cspi.createSinglePipePortItem("i", self),
            _cspi.createSinglePipePortItem("o", self),
            _cspi.createSinglePipePortItem("o", self),
        )

    def _setModels(self) -> None:
        inputPortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        output1PortItem = _mfn.PortItem("StrOut", _mfn.PortItemDirection.OUTPUT)
        output2PortItem = _mfn.PortItem("OrtOut", _mfn.PortItemDirection.OUTPUT)
        self._modelTeePiece = _mfn.TeePiece(inputPortItem, output1PortItem, output2PortItem)

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.TEE_PIECE_SVG

    def getInternalPiping(self) -> _ip.InternalPiping:
        modelPortItemsToGraphicalPortItem = {
            self._modelTeePiece.input: self.inputs[0],
            self._modelTeePiece.output1: self.outputs[0],
            self._modelTeePiece.output2: self.outputs[1],
        }
        internalPiping = _ip.InternalPiping([self._modelTeePiece], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        unitNumber = startingUnit

        unitText = _eh.getTeePieceUnit(
            unitNumber,
            self,
            self._modelTeePiece,
            _mfn.PortItemType.STANDARD,
            initialTemperature=20.0,
            componentName=self.displayName,
            extraNewlines="\n\n",
        )

        return unitText, unitNumber + 1

    def encode(self) -> _tp.Tuple[str, _dcj.JsonDict]:
        baseModel = self._encodeTeePieceBaseModel()

        teePieceModel = TeePieceModel(self.name, self.displayName, baseModel)

        dictName = "Block-"

        dct = teePieceModel.to_dict()

        return dictName, dct

    def decode(self, i: _dcj.JsonDict, resBlockList: list) -> None:
        model = TeePieceModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)

        baseModel = model.teePieceModel

        self._decodeTeePieceBaseModel(baseModel)

        resBlockList.append(self)

    @property
    def _portOffset(self):
        return 20


@_dc.dataclass
class TeePieceModelVersion1(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable=invalid-name
    BlockDisplayName: str  # pylint: disable=invalid-name
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable=invalid-name
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
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "TeePieceModelVersion1":
        assert isinstance(superseded, _bim.BlockItemModelVersion1)

        assert len(superseded.portsIdsIn) == 2
        assert len(superseded.portsIdsOut) == 1

        inputPortIds = [superseded.portsIdsIn[0]]
        outputPortIds = [superseded.portsIdsIn[1], superseded.portsIdsOut[0]]

        return TeePieceModelVersion1(
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


@_dc.dataclass
class TeePieceModel(_ser.UpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin):
    teePieceModel: _tpbm.TeePieceBaseModel

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,  # /NOSONAR
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> "TeePieceModel":
        teePieceModel = super().from_dict(data, validate, validate_enums, schema_type)
        return _tp.cast(TeePieceModel, teePieceModel)

    def to_dict(
        self,
        omit_none: bool = True,  # /NOSONAR
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code  # /NOSONAR
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums, schema_type)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return TeePieceModelVersion1

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "TeePieceModel":
        assert isinstance(superseded, TeePieceModelVersion1)

        baseModel = _tpbm.createTeePieceBaseModelFromLegacyModel(superseded)

        return TeePieceModel(superseded.BlockName, superseded.BlockDisplayName, baseModel)

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("d8a12235-c3f9-4742-bb7b-2c92a26d66c5")
