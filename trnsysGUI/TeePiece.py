# pylint: skip-file

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj
import pytrnsys.utils.serialization as _ser

import trnsysGUI.BlockItem as _bi
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.connection.names as _cnames
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _names
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps


class TeePiece(_bi.BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 40
        self.h = 40

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self._updateModels(self.displayName)

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    def hasDdckPlaceHolders(self) -> bool:
        return False

    def shallRenameOutputTemperaturesInHydraulicFile(self):
        return False

    def _updateModels(self, newDisplayName: str) -> None:
        input = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        output1 = _mfn.PortItem("StrOut", _mfn.PortItemDirection.OUTPUT)
        output2 = _mfn.PortItem("OrtOut", _mfn.PortItemDirection.OUTPUT)
        self._modelTeePiece = _mfn.TeePiece(input, output1, output2)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.TEE_PIECE_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        delta = 20
        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40

        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2

        deltaH = self.h / 8

        self.label.setPos(lx, h - self.flippedV * (h + h / 2))

        self.origInputsPos = [[0, delta]]
        self.origOutputsPos = [[w, delta], [delta, 0]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 1 - 2 * self.flippedV) % 4

        return w, h

    def getInternalPiping(self) -> _ip.InternalPiping:
        modelPortItemsToGraphicalPortItem = {
            self._modelTeePiece.input: self.inputs[0],
            self._modelTeePiece.output1: self.outputs[0],
            self._modelTeePiece.output2: self.outputs[1],
        }
        internalPiping = _ip.InternalPiping([self._modelTeePiece], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        f = ""
        unitNumber = startingUnit
        tNr = 929  # Temperature calculation from a tee-piece

        unitText = ""
        ambientT = 20

        equationConstant = 1

        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(tNr) + "\n"
        unitText += "!" + self.displayName + "\n"
        unitText += "PARAMETERS 0\n"
        unitText += "INPUTS 6\n"

        portItems = self._modelTeePiece.getPortItems()
        massFlowVariableNames = [
            _names.getMassFlowVariableName(self, self._modelTeePiece, portItems[0]),
            _names.getMassFlowVariableName(self, self._modelTeePiece, portItems[1]),
            _names.getMassFlowVariableName(self, self._modelTeePiece, portItems[2]),
        ]

        unitText += "\n".join(massFlowVariableNames) + "\n"

        temperatureVariableNames = [
            _cnames.getTemperatureVariableName(self.inputs[0].getConnection(), _mfn.PortItemType.STANDARD),
            _cnames.getTemperatureVariableName(self.outputs[0].getConnection(), _mfn.PortItemType.STANDARD),
            _cnames.getTemperatureVariableName(self.outputs[1].getConnection(), _mfn.PortItemType.STANDARD)
        ]

        unitText += "\n".join(temperatureVariableNames) + "\n"

        unitText += "***Initial values\n"
        unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

        unitText += "EQUATIONS 1\n"
        temperatureVariableName = _temps.getInternalTemperatureVariableName(self, self._modelTeePiece)
        unitText += f"{temperatureVariableName}= [{unitNumber},{equationConstant}]\n"

        unitNumber += 1
        f += unitText + "\n"

        return f, unitNumber

    def _getTemperatureVariableName(self, portItem: _pib.PortItemBase) -> str:
        connection = portItem.connectionList[0]
        node = connection.getInternalPiping().getNode(portItem, _mfn.PortItemType.STANDARD)
        temperatureVariableName = _temps.getTemperatureVariableName(connection, node)
        return temperatureVariableName

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


@_dc.dataclass
class TeePieceModel(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    BlockName: str
    BlockDisplayName: str
    blockPosition: _tp.Tuple[float, float]
    Id: int
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
        validate_enums: bool = True,
    ) -> "TeePieceModel":
        teePieceModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(TeePieceModel, teePieceModel)

    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code
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
