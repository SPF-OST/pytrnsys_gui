import typing as _tp

import dataclasses_jsonschema as _dcj

import trnsysGUI.BlockItem as _bi
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.common as _com
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps
from . import _defaults
from . import _serialization as _ser


class Pump(_bi.BlockItem, _ip.HasInternalPiping):  # pylint: disable=too-many-instance-attributes
    def __init__(self, trnsysType, editor, **kwargs):
        super().__init__(trnsysType, editor, **kwargs)
        self.w = 40
        self.h = 40

        self.massFlowRateInKgPerH = _defaults.DEFAULT_MASS_FLOW_RATE

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
        temperatureVariableName = _temps.getTemperatureVariableName(
            self.shallRenameOutputTemperaturesInHydraulicFile(),
            componentDisplayName=self.displayName,
            nodeName=self._modelPump.name,
        )
        inputConnection = self.inputs[0].getConnection()
        inputConnectionNode = inputConnection.getInternalPiping().getNode(self.inputs[0], _mfn.PortItemType.STANDARD)
        inputTemperatureVariable = _temps.getTemperatureVariableName(
            inputConnection.shallRenameOutputTemperaturesInHydraulicFile(),
            componentDisplayName=inputConnection.getDisplayName(),
            nodeName=inputConnectionNode.name,
        )
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
        position = (self.pos().x(), self.pos().y())

        blockItemModel = _ser.BlockItemBaseModel(
            self.name,
            self.displayName,
            position,
            self.id,
            self.trnsysId,
            self.flippedH,
            self.flippedV,
            self.rotationN,
        )

        blockItemWithPrescribedMassFlowModel = _ser.BlockItemWithPrescribedMassFlowBaseModel(
            blockItemModel,
            self.massFlowRateInKgPerH,
        )

        inputPortId = self._getSinglePortId(self.inputs)
        outputPortId = self._getSinglePortId(self.outputs)

        pumpModel = _ser.PumpModel(
            blockItemWithPrescribedMassFlowModel,
            inputPortId,
            outputPortId,
        )

        return "Block-", pumpModel.to_dict()

    @staticmethod
    def _getSinglePortId(ports: _tp.Sequence[_pib.PortItemBase]) -> int:
        port = _com.getSingle(ports)
        return port.id

    def decode(self, i: _dcj.JsonDict, resBlockList) -> None:
        model = _ser.PumpModel.from_dict(i)

        blockItemModel = model.blockItemWithPrescribedMassFlow.blockItem
        self.setDisplayName(blockItemModel.BlockDisplayName)
        self.setPos(float(blockItemModel.blockPosition[0]), float(blockItemModel.blockPosition[1]))
        self.id = blockItemModel.Id
        self.trnsysId = blockItemModel.trnsysId
        self.updateFlipStateH(blockItemModel.flippedH)
        self.updateFlipStateV(blockItemModel.flippedV)
        self.rotateBlockToN(blockItemModel.rotationN)

        self.massFlowRateInKgPerH = model.blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

        self.inputs[0].id = model.inputPortId
        self.outputs[0].id = model.outputPortId

        resBlockList.append(self)
