# pylint: skip-file

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.connection.connectors.doublePipeConnectorBase as _dpcb
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.globalNames as _gnames
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.serialization as _gser
import trnsysGUI.teePieces.exportHelper as _eh
import trnsysGUI.teePieces.teePieceBase as _tpb


class DoublePipeTeePiece(_tpb.TeePieceBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.w = 60
        self.h = 40

        self.changeSize()

        self.childIds = (self.trnsysId, self.editor.idGen.getTrnsysID())

        self._updateModels(self.displayName)

    def _createInputAndOutputPorts(self) -> _tp.Tuple[_pib.PortItemBase, _pib.PortItemBase, _pib.PortItemBase]:
        return (
            _dppi.DoublePipePortItem("i", 0, self),
            _dppi.DoublePipePortItem("o", 2, self),
            _dppi.DoublePipePortItem("o", 2, self),
        )

    def _updateModels(self, newDisplayName: str) -> None:
        coldInput: _mfn.PortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
        coldOutput1: _mfn.PortItem = _mfn.PortItem("StrOut", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
        coldOutput2: _mfn.PortItem = _mfn.PortItem("OrtOut", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
        self._coldTeePiece = _mfn.TeePiece(coldInput, coldOutput1, coldOutput2, name="Cold")

        hotInput: _mfn.PortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
        hotOutput1: _mfn.PortItem = _mfn.PortItem("StrOut", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
        hotOutput2: _mfn.PortItem = _mfn.PortItem("OrtOut", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
        self._hotTeePiece = _mfn.TeePiece(hotInput, hotOutput1, hotOutput2, name="Hot")

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        rotationAngle = (self.rotationN % 4) * 90

        if rotationAngle == 0:
            return _img.DP_TEE_PIECE_SVG

        if rotationAngle == 90:
            return _img.DP_TEE_PIECE_ROTATED_90

        if rotationAngle == 180:
            return _img.DP_TEE_PIECE_ROTATED_180

        if rotationAngle == 270:
            return _img.DP_TEE_PIECE_ROTATED_270

        raise AssertionError("Invalid rotation angle.")

    def encode(self) -> _tp.Tuple[str, _dcj.JsonDict]:
        blockItemModel = self._encodeBaseModel()

        childTrnsysIds = (self.childIds[0], self.childIds[1])
        inputPortId = self.inputs[0].id
        outputPortIds = (self.outputs[0].id, self.outputs[1].id)

        doublePipeTeePieceModel = DoublePipeTeePieceModel(
            self.name,
            self.displayName,
            blockItemModel,
            childTrnsysIds,
            inputPortId,
            outputPortIds,
        )

        dictName = "Block-"
        return dictName, doublePipeTeePieceModel.to_dict()

    def decode(self, i, resBlockList) -> None:
        model = DoublePipeTeePieceModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)

        self.childIds = model.childTrnsysIds

        self.inputs[0].id = model.inputPortId
        self.outputs[0].id = model.outputPortIds[0]
        self.outputs[1].id = model.outputPortIds[1]

        self._decodeBaseModel(model.blockItemModel)

        resBlockList.append(self)

    def getInternalPiping(self) -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self._coldTeePiece.input: self.inputs[0],
            self._coldTeePiece.output1: self.outputs[0],
            self._coldTeePiece.output2: self.outputs[1],
        }

        hotModelPortItemsToGraphicalPortItem = {
            self._hotTeePiece.input: self.inputs[0],
            self._hotTeePiece.output1: self.outputs[0],
            self._hotTeePiece.output2: self.outputs[1],
        }

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem

        internalPiping = _ip.InternalPiping([self._coldTeePiece, self._hotTeePiece], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):  # pylint: disable=too-many-locals
        unitNumber = startingUnit

        coldComponentName = f"{self.displayName}{self._coldTeePiece.name}"
        coldUnitText = _eh.getTeePieceUnit(
            unitNumber,
            self,
            self._coldTeePiece,
            _mfn.PortItemType.COLD,
            _gnames.DoublePipes.INITIAL_COLD_TEMPERATURE,
            componentName=coldComponentName,
            extraNewlines="",
        )

        hotComponentName = f"{self.displayName}{self._hotTeePiece.name}"
        hotUnitText = _eh.getTeePieceUnit(
            unitNumber + 1,
            self,
            self._hotTeePiece,
            _mfn.PortItemType.HOT,
            _gnames.DoublePipes.INITIAL_HOT_TEMPERATURE,
            componentName=hotComponentName,
            extraNewlines="",
        )

        unitText = f"""\
! {self.displayName}
! cold side
{coldUnitText}
! hot side
{hotUnitText}


"""

        return unitText, unitNumber + 2

    @property
    def _portOffset(self):
        return 30


@_dc.dataclass
class DoublePipeTeePieceModelVersion0(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
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
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return _dpcb.DoublePipeBlockItemModelVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "DoublePipeTeePieceModelVersion0":
        assert isinstance(superseded, _dpcb.DoublePipeBlockItemModelVersion0)

        assert len(superseded.portsIdsIn) == 2
        assert len(superseded.portsIdsOut) == 1

        inputPortIds = [superseded.portsIdsIn[0]]
        outputPortIds = [superseded.portsIdsIn[1], superseded.portsIdsOut[0]]

        return DoublePipeTeePieceModelVersion0(
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.blockPosition,
            superseded.id,
            superseded.trnsysId,
            superseded.childIds,
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
class DoublePipeTeePieceModel(_ser.UpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin):
    blockItemModel: _bim.BlockItemBaseModel
    childTrnsysIds: _tp.Tuple[int, int]
    inputPortId: int
    outputPortIds: _tp.Tuple[int, int]

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,  # pylint: disable=duplicate-code
        validate_enums: bool = True,  # /NOSONAR
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> "DoublePipeTeePieceModel":
        doublePipeTeePieceModel = super().from_dict(data, validate, validate_enums, schema_type)
        return _tp.cast(DoublePipeTeePieceModel, doublePipeTeePieceModel)

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
        return DoublePipeTeePieceModelVersion0

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "DoublePipeTeePieceModel":
        assert isinstance(superseded, DoublePipeTeePieceModelVersion0)

        blockItemModel = _bim.createBlockItemBaseModelFromLegacyModel(superseded)

        assert len(superseded.childIds) == 2
        chidTrnsysIds = (superseded.childIds[0], superseded.childIds[1])

        assert len(superseded.portsIdsIn) == 1
        inputPortId = superseded.portsIdsIn[0]

        assert len(superseded.portsIdsOut) == 2
        outputPortIds = (superseded.portsIdsOut[0], superseded.portsIdsOut[1])

        return DoublePipeTeePieceModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            blockItemModel,
            chidTrnsysIds,
            inputPortId,
            outputPortIds,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("2864bcb3-172b-47dd-b4cf-20ad9ac97384")
