import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.BlockItem as _bi
import trnsysGUI.internalPiping as _ip
import trnsysGUI.temperatures as _temps

_DEFAULT_MASS_FLOW_RATE = 500


class Pump(_bi.BlockItem, _ip.HasInternalPiping):  # pylint: disable=too-many-instance-attributes
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)
        self.w = 40
        self.h = 40

        self.massFlowRateInKgPerH = _DEFAULT_MASS_FLOW_RATE

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        self._modelPump = _mfn.Pump(inputPort, outputPort)

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    def hasDdckPlaceHolders(self) -> bool:
        return False

    def shallRenameOutputTemperaturesInHydraulicFile(self):
        return False

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.PUMP_SVG

    def changeSize(self):
        width = self.w
        height = self.h

        delta = 20

        height = min(height, 20)
        width = min(width, 40)

        rect = self.label.boundingRect()
        labelWidth = rect.width()
        labelPosX = (width - labelWidth) / 2
        self.label.setPos(labelPosX, height)

        self.origInputsPos = [[0, delta]]
        self.origOutputsPos = [[width, delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return width, height

    def exportPumpOutlets(self):
        temperatureVariableName = _temps.getTemperatureVariableName(self, self._modelPump)
        inputConnection = self.inputs[0].getConnection()
        inputConnectionNode = inputConnection.getInternalPiping().getNode(self.inputs[0], _mfn.PortItemType.STANDARD)
        inputTemperatureVariable = _temps.getTemperatureVariableName(inputConnection, inputConnectionNode)
        equation = f"{temperatureVariableName} = {inputTemperatureVariable}\n"
        equationNr = 1
        return equation, equationNr

    def exportMassFlows(self):
        equationNr = 1
        massFlowLine = f"Mfr{self.displayName} = {self.massFlowRateInKgPerH}\n"
        return massFlowLine, equationNr

    def getInternalPiping(self) -> _ip.InternalPiping:
        modelPortItemsToGraphicalPortItem = {
            self._modelPump.fromPort: self.inputs[0],
            self._modelPump.toPort: self.outputs[0],
        }
        return _ip.InternalPiping([self._modelPump], modelPortItemsToGraphicalPortItem)

    def encode(self) -> _tp.Tuple[str, _dcj.JsonDict]:
        inputPortIds = [p.id for p in self.inputs]
        outputPortIds = [p.id for p in self.outputs]
        position = (self.pos().x(), self.pos().y())

        pumpModel = PumpModel(
            self.name,
            self.displayName,
            position,
            self.id,
            self.trnsysId,
            inputPortIds,
            outputPortIds,
            self.flippedH,
            self.flippedV,
            self.rotationN,
            self.massFlowRateInKgPerH,
        )

        return "Block-", pumpModel.to_dict()

    def decode(self, i: _dcj.JsonDict, resBlockList) -> None:
        model = PumpModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)
        self.setPos(float(model.blockPosition[0]), float(model.blockPosition[1]))
        self.id = model.Id
        self.trnsysId = model.trnsysId

        self.inputs[0].id = model.portsIdsIn[0]
        self.outputs[0].id = model.portsIdsOut[0]

        self.updateFlipStateH(model.flippedH)
        self.updateFlipStateV(model.flippedV)
        self.rotateBlockToN(model.rotationN)

        self.massFlowRateInKgPerH = model.massFlowRateInKgPerH

        resBlockList.append(self)


@_dc.dataclass
class PumpModel(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable=invalid-name
    BlockDisplayName: str  # pylint: disable=invalid-name
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable=invalid-name,duplicate-code # 1
    trnsysId: int
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    massFlowRateInKgPerH: float

    @classmethod
    def from_dict(
        cls,  # pylint: disable = duplicate-code 2
        data: _dcj.JsonDict,  # pylint: disable = duplicate-code 2
        validate=True,
        validate_enums: bool = True,
    ) -> "PumpModel":
        pumpModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(PumpModel, pumpModel)

    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code 2
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return _bim.BlockItemModel

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "PumpModel":
        assert isinstance(superseded, _bim.BlockItemModel)

        return PumpModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.blockPosition,
            superseded.Id,
            superseded.trnsysId,
            superseded.portsIdsIn,
            superseded.portsIdsOut,
            superseded.flippedH,
            superseded.flippedV,
            superseded.rotationN,
            _DEFAULT_MASS_FLOW_RATE,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("9552365f-ef11-4fac-ba35-644e94b54088")
