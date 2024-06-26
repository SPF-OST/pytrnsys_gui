import dataclasses as _dc

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res

import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.dialogs as _dlgs
import trnsysGUI.warningsAndErrors as _werrors
import trnsysGUI.names.rename as _rename

_dlgs.assertThatLocalGeneratedUIModuleAndResourcesExist(__name__)

from . import _UI_dialog_generated as _gen  # pylint: disable=wrong-import-position


@_dc.dataclass
class Model:
    name: str
    isHorizontallyFlipped: bool
    isVerticallyFlipped: bool
    massFlowRateKgPerH: float


class Dialog(_qtw.QDialog, _gen.Ui_dialog):
    def __init__(self, model: Model, renameHelper: _rename.RenameHelper) -> None:
        super().__init__()
        self.setupUi(self)

        self._model = _dc.replace(model)
        self._renameHelper = renameHelper
        self._updateDialogFromModel()

        self._configure()

    @staticmethod
    def showDialogAndGetResult(model: Model, renameHelper: _rename.RenameHelper) -> _cancel.MaybeCancelled[Model]:
        dialog = Dialog(model, renameHelper)

        returnCode = dialog.exec()
        if returnCode == _qtw.QDialog.Rejected:
            return _cancel.CANCELLED

        return dialog._model  # pylint: disable=protected-access

    def _updateDialogFromModel(self) -> None:
        self.nameLineEdit.setText(self._model.name)
        self.massFlowLineEdit.setText(str(self._model.massFlowRateKgPerH))
        self.flipVerticallyCheckBox.setChecked(self._model.isVerticallyFlipped)
        self.flipHorizontallyCheckBox.setChecked(self._model.isHorizontallyFlipped)

    def _configure(self):
        self.nameLineEdit.editingFinished.connect(self._onNameLineEditEditingFinished)
        self.massFlowLineEdit.editingFinished.connect(self._onMassFlowLineEditEditingFinished)
        self.flipHorizontallyCheckBox.stateChanged.connect(self._onFlipHorizontallyCheckBoxStateChanged)
        self.flipVerticallyCheckBox.stateChanged.connect(self._onFlipVerticallyCheckBoxStateChanged)

    def _onNameLineEditEditingFinished(self) -> None:
        newNameCandidate = self.nameLineEdit.text()
        currentName = self._model.name

        checkDdckFolder = False
        result = self._renameHelper.canRename(currentName, newNameCandidate, checkDdckFolder)
        if _res.isError(result):
            error = _res.error(result)
            _werrors.showMessageBox(error.message)
        else:
            self._model.name = newNameCandidate

        self._updateDialogFromModel()

    def _onMassFlowLineEditEditingFinished(self) -> None:
        text = self.massFlowLineEdit.text()

        try:
            newMassFlowCandidate = float(text)
        except ValueError:
            newMassFlowCandidate = None

        if newMassFlowCandidate is None:
            _werrors.showMessageBox(message="Mass flow must be a number.", title="Invalid value")
        else:
            self._model.massFlowRateKgPerH = newMassFlowCandidate

        self._updateDialogFromModel()

    def _onFlipHorizontallyCheckBoxStateChanged(self, newState: int) -> None:
        self._model.isHorizontallyFlipped = self._isChecked(newState)
        self._updateDialogFromModel()

    def _onFlipVerticallyCheckBoxStateChanged(self, newState: int) -> None:
        self._model.isVerticallyFlipped = self._isChecked(newState)
        self._updateDialogFromModel()

    @staticmethod
    def _isChecked(checkState: int):
        assert checkState in (_qtc.Qt.Checked, _qtc.Qt.Unchecked)

        isChecked = checkState == _qtc.Qt.Checked

        return isChecked
