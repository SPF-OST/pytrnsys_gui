import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.names.rename as _rename
from trnsysGUI import BlockItem as _bi
from trnsysGUI import common as _com
from trnsysGUI import internalPiping as _ip
from trnsysGUI.pumpsAndTaps import _defaults
from trnsysGUI.pumpsAndTaps import _dialog
from trnsysGUI.pumpsAndTaps import _serialization as _ser


class PumpsAndTabsBase(_bi.BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self._renameHelper = _rename.RenameHelper(editor.namesManager)

        self.w = 40
        self.h = 40

        self._massFlowRateInKgPerH = _defaults.DEFAULT_MASS_FLOW_RATE

    def getInternalPiping(self) -> _ip.InternalPiping:
        raise NotImplementedError()

    def getDisplayName(self) -> str:
        return self.displayName

    @classmethod
    @_tp.override
    def shallRenameOutputTemperaturesInHydraulicFile(cls) -> bool:
        return False

    def _getCanonicalMassFlowRate(self) -> float:
        raise NotImplementedError()

    def exportMassFlows(self) -> _tp.Tuple[str, int]:
        internalPiping = self.getInternalPiping()
        node = _com.getSingle(internalPiping.nodes)
        inputVariableName = _mnames.getInputVariableName(self, node)
        canonicalMassFlowRate = self._getCanonicalMassFlowRate()
        result = f"{inputVariableName} = {canonicalMassFlowRate}\n"
        equationNr = 1
        return result, equationNr

    def _createBlockItemWithPrescribedMassFlowForEncode(self) -> _ser.BlockItemWithPrescribedMassFlowBaseModel:
        blockItemModel = self._encodeBaseModel()

        blockItemWithPrescribedMassFlowModel = _ser.BlockItemWithPrescribedMassFlowBaseModel(
            blockItemModel,
            self._massFlowRateInKgPerH,
        )

        return blockItemWithPrescribedMassFlowModel

    def _applyBlockItemModelWithPrescribedMassFlowForDecode(
        self, blockItemWithPrescribedMassFlow: _ser.BlockItemWithPrescribedMassFlowBaseModel
    ) -> None:
        blockItemModel = blockItemWithPrescribedMassFlow.blockItem
        self._decodeBaseModel(blockItemModel)

        self._massFlowRateInKgPerH = blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

    def mouseDoubleClickEvent(self, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        dialogModel = _dialog.Model(self.displayName, self.flippedH, self.flippedV, self._massFlowRateInKgPerH)

        maybeCancelled = _dialog.Dialog.showDialogAndGetResult(dialogModel, self._renameHelper)
        if _cancel.isCancelled(maybeCancelled):
            return

        newDialogModel = _cancel.value(maybeCancelled)

        self._renameHelper.rename(dialogModel.name, newDialogModel.name)

        self.setDisplayName(newDialogModel.name)
        self.updateFlipStateH(newDialogModel.isHorizontallyFlipped)
        self.updateFlipStateV(newDialogModel.isVerticallyFlipped)
        self._massFlowRateInKgPerH = newDialogModel.massFlowRateKgPerH
