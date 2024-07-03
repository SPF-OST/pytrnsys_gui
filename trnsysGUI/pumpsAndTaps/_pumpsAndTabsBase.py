import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.common as _com
import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.names.rename as _rename
import trnsysGUI.pumpsAndTaps.defaults as _defaults
from . import _dialog
from . import serialization as _ser


class PumpsAndTabsBase(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self._renameHelper = _rename.RenameHelper(editor.namesManager)

        self.w = 40
        self.h = 40

        self.massFlowRateInKgPerH = _defaults.DEFAULT_MASS_FLOW_RATE

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        raise NotImplementedError()

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
            self.massFlowRateInKgPerH,
        )

        return blockItemWithPrescribedMassFlowModel

    def _applyBlockItemModelWithPrescribedMassFlowForDecode(
        self, blockItemWithPrescribedMassFlow: _ser.BlockItemWithPrescribedMassFlowBaseModel
    ) -> None:
        blockItemModel = blockItemWithPrescribedMassFlow.blockItem
        self._decodeBaseModel(blockItemModel)

        self.massFlowRateInKgPerH = blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

    def mouseDoubleClickEvent(self, event: _qtw.QGraphicsSceneMouseEvent) -> None:
        dialogModel = _dialog.Model(self.displayName, self.flippedH, self.flippedV, self.massFlowRateInKgPerH)

        maybeCancelled = _dialog.Dialog.showDialogAndGetResult(dialogModel, self._renameHelper)
        if _cancel.isCancelled(maybeCancelled):
            return

        newDialogModel = _cancel.value(maybeCancelled)

        self._renameHelper.rename(dialogModel.name, newDialogModel.name)

        self.setDisplayName(newDialogModel.name)
        self.updateFlipStateH(newDialogModel.isHorizontallyFlipped)
        self.updateFlipStateV(newDialogModel.isVerticallyFlipped)
        self.massFlowRateInKgPerH = newDialogModel.massFlowRateKgPerH
