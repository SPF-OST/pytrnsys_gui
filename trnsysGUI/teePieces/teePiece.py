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
import trnsysGUI.teePieces.exportHelper as _eh
import trnsysGUI.teePieces.teePieceBase as _tpb


class TeePiece(_tpb.TeePieceBase):
    def __init__(self, trnsysType, editor, **kwargs):
        super().__init__(trnsysType, editor, **kwargs)

        self._updateModels(self.displayName)

        self.changeSize()

    def _createInputAndOutputPorts(self) -> _tp.Tuple[_pib.PortItemBase, _pib.PortItemBase, _pib.PortItemBase]:
        return (
            _cspi.createSinglePipePortItem("i", 0, self),
            _cspi.createSinglePipePortItem("o", 2, self),
            _cspi.createSinglePipePortItem("o", 2, self),
        )

    def _updateModels(self, newDisplayName: str) -> None:
        inputPortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        output1PortItem = _mfn.PortItem("StrOut", _mfn.PortItemDirection.OUTPUT)
        output2PortItem = _mfn.PortItem("OrtOut", _mfn.PortItemDirection.OUTPUT)
        self._modelTeePiece = _mfn.TeePiece(inputPortItem, output1PortItem, output2PortItem)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
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

    def encode(self):
        portListInputs = []
        portListOutputs = []

        for inp in self.inputs:
            portListInputs.append(inp.id)
        for output in self.outputs:
            portListOutputs.append(output.id)

        blockPosition = (float(self.pos().x()), float(self.pos().y()))

        teePieceModel = TeePieceModel(
            self.name,
            self.displayName,
            blockPosition,
            self.id,
            self.trnsysId,
            portListInputs,
            portListOutputs,
            self.flippedH,
            self.flippedV,
            self.rotationN,
        )

        dictName = "Block-"

        dct = teePieceModel.to_dict()

        return dictName, dct

    def decode(self, i, resBlockList):
        model = TeePieceModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)
        self.setPos(float(model.blockPosition[0]), float(model.blockPosition[1]))
        self.id = model.Id
        self.trnsysId = model.trnsysId

        self.inputs[0].id = model.portsIdsIn[0]
        self.outputs[0].id = model.portsIdsOut[0]
        self.outputs[1].id = model.portsIdsOut[1]

        self.updateFlipStateH(model.flippedH)
        self.updateFlipStateV(model.flippedV)
        self.rotateBlockToN(model.rotationN)

        resBlockList.append(self)

    @property
    def _portOffset(self):
        return 20


@_dc.dataclass
class TeePieceModel(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
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
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,  # /NOSONAR
    ) -> "TeePieceModel":
        teePieceModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(TeePieceModel, teePieceModel)

    def to_dict(
        self,
        omit_none: bool = True,  # /NOSONAR
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code  # /NOSONAR
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return _bim.BlockItemModel

    @classmethod
    def upgrade(cls, superseded: _bim.BlockItemModel) -> "TeePieceModel":  # type: ignore[override]
        assert len(superseded.portsIdsIn) == 2
        assert len(superseded.portsIdsOut) == 1

        inputPortIds = [superseded.portsIdsIn[0]]
        outputPortIds = [superseded.portsIdsIn[1], superseded.portsIdsOut[0]]

        return TeePieceModel(
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