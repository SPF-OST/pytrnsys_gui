# pylint: skip-file

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj
import pytrnsys.utils.serialization as _ser

import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.connectors.doublePipeConnectorBase import DoublePipeBlockItemModel
from trnsysGUI.doublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]


class DoublePipeTeePiece(BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 60
        self.h = 40

        self.inputs.append(DoublePipePortItem("i", 0, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))

        self.changeSize()

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self._updateModels(self.displayName)

    def getDisplayName(self) -> str:
        return self.displayName

    def hasDdckPlaceHolders(self) -> bool:
        return False

    def shallRenameOutputTemperaturesInHydraulicFile(self):
        return False

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

    def changeSize(self):
        width, _ = self._getCappedWithAndHeight()
        self._positionLabel()

        self.origInputsPos = [[0, 30]]
        self.origOutputsPos = [[width, 30], [30, 0]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        # pylint: disable=duplicate-code  # 1
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        # pylint: disable=duplicate-code  # 1
        self.outputs[1].side = (self.rotationN + 1 - 2 * self.flippedV) % 4

    def encode(self):
        portListInputs = []
        portListOutputs = []

        for inp in self.inputs:
            portListInputs.append(inp.id)
        for output in self.outputs:
            portListOutputs.append(output.id)

        blockPosition = (float(self.pos().x()), float(self.pos().y()))

        doublePipeTeePieceModel = DoublePipeTeePieceModel(
            self.name,
            self.displayName,
            blockPosition,
            self.id,
            self.trnsysId,
            self.childIds,
            portListInputs,
            portListOutputs,
            self.flippedH,
            self.flippedV,
            self.rotationN,
        )

        dictName = "Block-"
        return dictName, doublePipeTeePieceModel.to_dict()

    def decode(self, i, resBlockList):
        model = DoublePipeTeePieceModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)
        self.setPos(float(model.blockPosition[0]), float(model.blockPosition[1]))
        self.id = model.id
        self.trnsysId = model.trnsysId
        self.childIds = model.childIds

        self.inputs[0].id = model.portsIdsIn[0]
        self.outputs[0].id = model.portsIdsOut[0]
        self.outputs[1].id = model.portsIdsOut[1]

        self.updateFlipStateH(model.flippedH)
        self.updateFlipStateV(model.flippedV)
        self.rotateBlockToN(model.rotationN)

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
        tNr = 929  # Temperature calculation from a tee-piece

        unitText = ""
        ambientT = 20
        equationConstant = 1

        unitNumber, unitText = self._getExport(
            ambientT, equationConstant, self._coldTeePiece, tNr, "Cold", unitNumber, unitText
        )
        unitNumber, unitText = self._getExport(
            ambientT, equationConstant, self._hotTeePiece, tNr, "Hot", unitNumber, unitText
        )
        return unitText, unitNumber

    def _getExport(self, ambientT, equationConstant, teePiece, tNr, temperature, unitNumber, unitText):
        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(tNr) + "\n"
        unitText += "!" + self.displayName + temperature + "\n"
        unitText += "PARAMETERS 0\n"
        unitText += "INPUTS 6\n"

        portItems = teePiece.getPortItems()
        massFlowVariableNames = [
            _mnames.getMassFlowVariableName(self, teePiece, portItems[0]),
            _mnames.getMassFlowVariableName(self, teePiece, portItems[1]),
            _mnames.getMassFlowVariableName(self, teePiece, portItems[2]),
        ]

        unitText += "\n".join(massFlowVariableNames) + "\n"

        unitText += f"T{self.inputs[0].connectionList[0].displayName}{temperature}\n"
        unitText += f"T{self.outputs[0].connectionList[0].displayName}{temperature}\n"
        unitText += f"T{self.outputs[1].connectionList[0].displayName}{temperature}\n"

        unitText += "***Initial values\n"
        unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

        unitText += "EQUATIONS 1\n"
        unitText += (
            "T" + self.displayName + temperature + "= [" + str(unitNumber) + "," + str(equationConstant) + "]\n\n"
        )
        unitNumber += 1

        return unitNumber, unitText


@_dc.dataclass
class DoublePipeTeePieceModel(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
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
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,  # pylint: disable=duplicate-code
        validate_enums: bool = True,
    ) -> "DoublePipeTeePieceModel":
        doublePipeTeePieceModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(DoublePipeTeePieceModel, doublePipeTeePieceModel)

    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)  # pylint: disable=duplicate-code
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return DoublePipeBlockItemModel

    @classmethod
    def upgrade(cls, superseded: DoublePipeBlockItemModel) -> "DoublePipeTeePieceModel":  # type: ignore[override]
        assert len(superseded.portsIdsIn) == 2
        assert len(superseded.portsIdsOut) == 1

        inputPortIds = [superseded.portsIdsIn[0]]
        outputPortIds = [superseded.portsIdsIn[1], superseded.portsIdsOut[0]]

        return DoublePipeTeePieceModel(
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
