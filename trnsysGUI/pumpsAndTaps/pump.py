import typing as _tp

import dataclasses_jsonschema as _dcj

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.common as _com
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps
from . import _pumpsAndTabsBase as _patb
from . import _serialization as _ser


class Pump(_patb.PumpsAndTabsBase):  # pylint: disable=too-many-instance-attributes
    def __init__(self, trnsysType, editor, **kwargs):
        super().__init__(trnsysType, editor, **kwargs)

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        self._modelPump = _mfn.Pump(inputPort, outputPort)

        self.changeSize()

    def getInternalPiping(self) -> _ip.InternalPiping:
        modelPortItemsToGraphicalPortItem = {
            self._modelPump.fromPort: self.inputs[0],
            self._modelPump.toPort: self.outputs[0],
        }
        return _ip.InternalPiping([self._modelPump], modelPortItemsToGraphicalPortItem)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.PUMP_SVG

    def _getCanonicalMassFlowRate(self) -> float:
        return self._massFlowRateInKgPerH

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

    def encode(self) -> _tp.Tuple[str, _dcj.JsonDict]:
        blockItemWithPrescribedMassFlowModel = self._createBlockItemWithPrescribedMassFlowForEncode()

        inputPortId = self._getSinglePortId(self.inputs)
        outputPortId = self._getSinglePortId(self.outputs)

        pumpModel = _ser.PumpModel(
            self.name,
            self.displayName,
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

        assert model.BlockName == self.name

        self.setDisplayName(model.BlockDisplayName)

        self._applyBlockItemModelWithPrescribedMassFlowForDecode(model.blockItemWithPrescribedMassFlow)

        self.inputs[0].id = model.inputPortId
        self.outputs[0].id = model.outputPortId

        resBlockList.append(self)

    def changeSize(self) -> _tp.Tuple[int, int]:
        width = self.w
        height = self.h

        height = min(height, 20)
        width = min(width, 40)

        rect = self.label.boundingRect()
        labelWidth = rect.width()
        labelPosX = (width - labelWidth) / 2
        self.label.setPos(labelPosX, height)

        delta = 20
        self.origInputsPos = [[0, delta]]
        self.origOutputsPos = [[width, delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return width, height
