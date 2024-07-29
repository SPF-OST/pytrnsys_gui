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

        self._configureComponentcomponentComboBox(hasInternalPipings)

        componentName = outputFilePath.parent.name
        currentIndex = self.componentComboBox.findText(componentName, _qtc.Qt.MatchContains)
        currentIndex = max(0, currentIndex)
        self.componentComboBox.setCurrentIndex(currentIndex)
        currentInternalPiping = self.componentComboBox.currentData()

        self.dialogResult = DialogResult(currentInternalPiping, outputFilePath)

        self.okCancelButtonBox.accepted.connect(self.accept)
        self.okCancelButtonBox.rejected.connect(self.reject)

    def _configureComponentcomponentComboBox(self, hasInternalPipings: _cabc.Sequence[_ip.HasInternalPiping]) -> None:
        def getDisplayName(hip: _ip.HasInternalPiping) -> str:
            return hip.getDisplayName()

        sortedHasInternalPiping = sorted(hasInternalPipings, key=getDisplayName)
        for hasInternalPiping in sortedHasInternalPiping:
            displayName = hasInternalPiping.getDisplayName()
            internalPiping = hasInternalPiping.getInternalPiping()

            self.componentComboBox.addItem(displayName, internalPiping)
        self.componentComboBox.activated.connect(self._onActivated)

    def _onActivated(self, newIndex: int) -> None:
        newData = self.componentComboBox.itemData(newIndex)
        self.dialogResult.internalPiping = newData

    @staticmethod
    def showDialogAndGetResults(
        hasInternalPipings: _cabc.Sequence[_ip.HasInternalPiping], outputFilePath: _pl.Path
    ) -> _cancel.MaybeCancelled[DialogResult]:
        dialog = ConvertDialog(hasInternalPipings, outputFilePath)
        returnValue = dialog.exec()

        if returnValue == _qtw.QDialog.Rejected:
            return _cancel.CANCELLED

        return dialog.dialogResult
