import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.names.rename as _rename
from trnsysGUI import BlockItem as _bi, internalPiping as _ip, common as _com
from trnsysGUI.pumpsAndTaps import _defaults, _serialization as _ser, _dialog


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

    def shallRenameOutputTemperaturesInHydraulicFile(self) -> bool:
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
        position = (self.pos().x(), self.pos().y())
        blockItemModel = _ser.BlockItemBaseModel(
            position,
            self.id,
            self.trnsysId,
            self.flippedH,
            self.flippedV,
            self.rotationN,
        )
        blockItemWithPrescribedMassFlowModel = _ser.BlockItemWithPrescribedMassFlowBaseModel(
            blockItemModel,
            self._massFlowRateInKgPerH,
        )
        return blockItemWithPrescribedMassFlowModel

    def _applyBlockItemModelWithPrescribedMassFlowForDecode(
        self, blockItemWithPrescribedMassFlow: _ser.BlockItemWithPrescribedMassFlowBaseModel
    ) -> None:
        blockItemModel = blockItemWithPrescribedMassFlow.blockItem
        self.setPos(float(blockItemModel.blockPosition[0]), float(blockItemModel.blockPosition[1]))
        self.id = blockItemModel.Id
        self.trnsysId = blockItemModel.trnsysId
        self.updateFlipStateH(blockItemModel.flippedH)
        self.updateFlipStateV(blockItemModel.flippedV)
        self.rotateBlockToN(blockItemModel.rotationN)
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
