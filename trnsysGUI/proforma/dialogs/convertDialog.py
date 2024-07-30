import dataclasses as _dc
import pathlib as _pl
import collections.abc as _cabc

import PyQt5.QtWidgets as _qtw
import PyQt5.QtCore as _qtc

import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.dialogs as _dlgs
import trnsysGUI.internalPiping as _ip

_dlgs.assertThatLocalGeneratedUIModuleAndResourcesExist(__name__, moduleName="_UI_convert_generated")

from . import _UI_convert_generated as _uigen  # type: ignore[import]  # pylint: disable=wrong-import-position


@_dc.dataclass
class DialogResult:
    internalPiping: _ip.InternalPiping
    outputFilePath: _pl.Path


class ConvertDialog(_qtw.QDialog, _uigen.Ui_Convert):
    def __init__(self, hasInternalPipings: _cabc.Sequence[_ip.HasInternalPiping], outputFilePath: _pl.Path) -> None:
        super().__init__()
        self.setupUi(self)

        if not hasInternalPipings:
            raise ValueError("Must have at least one internal piping.")

        self.outputFilePathLineEdit.setText(str(outputFilePath))
        self.outputFilePathLineEdit.textChanged.connect(self._onOutputFilePathLineEditTextChanged)

        self._configureComponentComboBox(hasInternalPipings)

        componentName = outputFilePath.parent.name
        currentInternalPiping = self._setAndGetCurrentInternalPiping(componentName)

        self.dialogResult = DialogResult(currentInternalPiping, outputFilePath)

        self.chooseOutputFilePathPushButton.pressed.connect(self._onChooseOutputFilePathPushButtonPressed)

        self.okCancelButtonBox.accepted.connect(self.accept)
        self.okCancelButtonBox.rejected.connect(self.reject)

    def _configureComponentComboBox(self, hasInternalPipings: _cabc.Sequence[_ip.HasInternalPiping]) -> None:
        def getDisplayName(hip: _ip.HasInternalPiping) -> str:
            return hip.getDisplayName()

        sortedHasInternalPiping = sorted(hasInternalPipings, key=getDisplayName)
        for hasInternalPiping in sortedHasInternalPiping:
            displayName = hasInternalPiping.getDisplayName()
            internalPiping = hasInternalPiping.getInternalPiping()

            self.componentComboBox.addItem(displayName, internalPiping)

    def _setAndGetCurrentInternalPiping(self, componentName: str) -> _ip.InternalPiping:
        currentIndex = self.componentComboBox.findText(componentName, _qtc.Qt.MatchContains)
        currentIndex = max(0, currentIndex)
        self.componentComboBox.setCurrentIndex(currentIndex)
        currentInternalPiping = self.componentComboBox.currentData()
        return currentInternalPiping

    def _onOutputFilePathLineEditTextChanged(self, newText: str) -> None:
        self.dialogResult.outputFilePath = _pl.Path(newText)

    def _onChooseOutputFilePathPushButtonPressed(self) -> None:
        currentOutputFilePathString = self.outputFilePathLineEdit.text()

        newOutputFilePathString, _ = _qtw.QFileDialog.getSaveFileName(
            None, "Select ouput file path...", currentOutputFilePathString
        )

        if not newOutputFilePathString:
            return

        self.outputFilePathLineEdit.setText(newOutputFilePathString)

    @staticmethod
    def showDialogAndGetResults(
        hasInternalPipings: _cabc.Sequence[_ip.HasInternalPiping], outputFilePath: _pl.Path
    ) -> _cancel.MaybeCancelled[DialogResult]:
        dialog = ConvertDialog(hasInternalPipings, outputFilePath)
        returnValue = dialog.exec()

        if returnValue == _qtw.QDialog.Rejected:
            return _cancel.CANCELLED

        return dialog.dialogResult
