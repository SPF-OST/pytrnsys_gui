import collections.abc as _cabc
import typing as _tp

import dataclasses_jsonschema as _dcj

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.common as _com
import trnsysGUI.connection.hydraulicExport.singlePipe.createExportHydraulicSinglePipeConnection as _cehspc
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.hydraulicLoops.model as _hlmod
import trnsysGUI.hydraulicLoops.names as _names
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.singlePipePortItem as _spi
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

    @property
    def inputPort(self) -> _spi.SinglePipePortItem:
        return self._getSingleSinglePortItem(self.inputs)

    @property
    def outputPort(self) -> _spi.SinglePipePortItem:
        return self._getSingleSinglePortItem(self.outputs)

    def _getSingleSinglePortItem(
        self, portItems: _cabc.Sequence[_pib.PortItemBase]
    ) -> _spi.SinglePipePortItem:
        portItem = _com.getSingle(portItems)
        assert isinstance(portItem, _spi.SinglePipePortItem)
        return portItem

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

    def exportPumpConsumptionName(self) -> str:
        inputVariableName = _mnames.getInputVariableName(self, self._modelPump)
        return f"Pel{inputVariableName}_kW"

    def exportPumpPowerConsumption(self, loop: _hlmod.HydraulicLoop) -> str:
        mfrVarName = _mnames.getInputVariableName(self, self._modelPump)

        pElVarName = self.exportPumpConsumptionName()
        canonicalMassFlowRate = self._getCanonicalMassFlowRate()

        loopDensityGlobalVarName = f"${_names.getDensityName(loop.name.value)}"

        result = f"""\
***********************************************
*** Pump Consumption of {self.displayName}
***********************************************

EQUATIONS #
{mfrVarName}Nom = {canonicalMassFlowRate}  ! Nominal mass flow rate, kg/h.

! Pressure-drop of loop at nominal mass flow, bar
dpPu{mfrVarName}Nom_bar = MIN(dpmax_bar,MAX(dpmin_bar,{mfrVarName}Nom/{loopDensityGlobalVarName} * 0.1))

fr{mfrVarName} = ${mfrVarName}/{mfrVarName}Nom !  Flow rate fraction of nominal flow rate
dpPu{mfrVarName}_bar = fr{mfrVarName}^2*dpPu{mfrVarName}Nom_bar ! Pressure-drop of loop at actual mass flow, bar

! Required power to drive the flow in kW
Pflow{mfrVarName}_kW = ((${mfrVarName}/3600)/ {loopDensityGlobalVarName}) * dpPu{mfrVarName}_bar*100

eta{mfrVarName} = MAX(1E-3,0.85*(-0.60625*fr{mfrVarName}^2+1.25*fr{mfrVarName})) ! pump efficiency (electric 85 %)
{pElVarName} = GT(${mfrVarName},0.1)*Pflow{mfrVarName}_kW/eta{mfrVarName} !required pump electric power, kW
"""
        return result
