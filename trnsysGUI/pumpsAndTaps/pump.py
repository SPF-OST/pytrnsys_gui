import typing as _tp

import dataclasses_jsonschema as _dcj

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.common as _com
import trnsysGUI.connection.hydraulicExport.singlePipe.createExportHydraulicSinglePipeConnection as _cehspc
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
from . import _pumpsAndTabsBase as _patb
from . import serialization as _ser


class Pump(
    _patb.PumpsAndTabsBase
):  # pylint: disable=too-many-instance-attributes
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self._fromPort = _cspi.createSinglePipePortItem("i", self)
        self._toPort = _cspi.createSinglePipePortItem("o", self)

        self.inputs.append(self._fromPort)
        self.outputs.append(self._toPort)

        self.changeSize()

        self._setModels()

    def _setModels(self) -> None:
        modelInputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        modelOutputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        self._modelPump = _mfn.Pump(modelInputPort, modelOutputPort)

    def getInternalPiping(self) -> _ip.InternalPiping:
        modelPortItemsToGraphicalPortItem = {
            self._modelPump.fromPort: self._fromPort,
            self._modelPump.toPort: self._toPort,
        }
        return _ip.InternalPiping(
            [self._modelPump], modelPortItemsToGraphicalPortItem
        )

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return False

    @classmethod
    @_tp.override
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.PUMP_SVG

    def _getCanonicalMassFlowRate(self) -> float:
        return self.massFlowRateInKgPerH

    def encode(self) -> _tp.Tuple[str, _dcj.JsonDict]:
        blockItemWithPrescribedMassFlowModel = (
            self._createBlockItemWithPrescribedMassFlowForEncode()
        )

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

        self.inputs[0].id = model.inputPortId
        self.outputs[0].id = model.outputPortId

        self._applyBlockItemModelWithPrescribedMassFlowForDecode(
            model.blockItemWithPrescribedMassFlow
        )

        resBlockList.append(self)

    def exportPipeAndTeeTypesForTemp(
        self, startingUnit: int
    ) -> _tp.Tuple[str, int]:
        return _cehspc.exportDummySinglePipeConnection(
            self, startingUnit, self._fromPort, self._toPort, self._modelPump
        )

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
        self.inputs[0].setPos(
            self.origInputsPos[0][0], self.origInputsPos[0][1]
        )
        self.outputs[0].setPos(
            self.origOutputsPos[0][0], self.origOutputsPos[0][1]
        )

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        return width, height
