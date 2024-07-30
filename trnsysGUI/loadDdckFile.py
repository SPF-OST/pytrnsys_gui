import dataclasses as _dc
import pathlib as _pl
import shutil as _su

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res
import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.internalPiping as _ip
import trnsysGUI.proforma.convertXmlTmfToDdck as _pro
import trnsysGUI.proforma.createModelConnections as _pcmc
import trnsysGUI.proforma.dialogs.convertDialog as _pcd
import trnsysGUI.warningsAndErrors as _warn


@_dc.dataclass
class DdckFileLoader:
    hasInternalPipingsProvider: _ip.HasInternalPipingsProvider

    def loadDdckFile(self, targetDirPath: _pl.Path) -> None:
        if not targetDirPath.is_dir():
            raise ValueError("Not a directory.", targetDirPath)

        sourceFilePathString, _ = _qtw.QFileDialog.getOpenFileName(None, "Load file")
        if not sourceFilePathString:
            return

        sourceFilePath = _pl.Path(sourceFilePathString)

        isSourceProformaFile = self._isProformaFilePath(sourceFilePath)
        targetSuffix = ".ddck" if isSourceProformaFile else sourceFilePath.suffix

        targetFilePathStem = targetDirPath / sourceFilePath.stem
        targetFilePath = targetFilePathStem.with_suffix(targetSuffix)

        if targetFilePath.is_dir():
            message = f"""\
        A directory of the name `{targetFilePath.name}` already exists. Please change the name of the file before
        importing or remove the directory."""
            _warn.showMessageBox(message, _warn.Title.WARNING)
            return

        if targetFilePath.is_file():
            message = f"""\
                    A file of the name `{targetFilePath.name}` already exists. Do you want to overwrite it?"""

            standardButton = _qtw.QMessageBox.question(None, "Overwrite file?", message)
            if standardButton != _qtw.QMessageBox.StandardButton.Yes:  # pylint: disable=no-member
                return

        if not isSourceProformaFile:
            _su.copy(sourceFilePath, targetFilePath)
            return

        self._convertAndLoadProformaFileIntoFolder(sourceFilePath, targetFilePath)

    def _convertAndLoadProformaFileIntoFolder(self, sourceFilePath: _pl.Path, targetFilePath: _pl.Path) -> None:
        hasInternalPipingsWithDdckPlaceholders = [
            hip for hip in self.hasInternalPipingsProvider.getInternalPipings() if hip.hasDdckPlaceHolders()
        ]

        dialogMaybeCancelled = _pcd.ConvertDialog.showDialogAndGetResults(
            hasInternalPipingsWithDdckPlaceholders, targetFilePath
        )
        if _cancel.isCancelled(dialogMaybeCancelled):
            return
        dialogResult = _cancel.value(dialogMaybeCancelled)

        createConnectionsResult = _pcmc.createModelConnectionsFromInternalPiping(dialogResult.internalPiping)
        if _res.isError(createConnectionsResult):
            _warn.showMessageBox(_res.error(createConnectionsResult).message)
            return
        suggestedHydraulicConnections = _res.value(createConnectionsResult)

        maybeCancelled = _pro.convertXmltmfToDdck(
            sourceFilePath,
            suggestedHydraulicConnections,
            dialogResult.outputFilePath,
        )
        if _cancel.isCancelled(maybeCancelled):
            return
        result = _cancel.value(maybeCancelled)
        if _res.isError(result):
            _warn.showMessageBox(_res.error(result).message)
            return

    @staticmethod
    def _isProformaFilePath(filePath: _pl.Path) -> bool:
        return filePath.suffix == ".xmltmf"
