import os as _os
import pathlib as _pl
import shutil as _su

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.result as _res

import trnsysGUI.common.cancelled as _cancel
import trnsysGUI.proforma.convertXmlTmfToDdck as _pro
import trnsysGUI.proforma.models as _models
import trnsysGUI.warningsAndErrors as _warn


class FileSystemTreeView(_qtw.QTreeView):
    def __init__(self, rootDirPath: _pl.Path) -> None:
        super().__init__(parent=None)

        rootFolder = str(rootDirPath)

        self._model = _qtw.QFileSystemModel()
        self._model.setRootPath(rootFolder)

        self.setModel(self._model)

        rootModelIndex = self._model.index(rootFolder)
        self.setRootIndex(rootModelIndex)

    def mouseDoubleClickEvent(self, event: _qtg.QMouseEvent) -> None:  # pylint: disable=unused-argument
        self._openCurrentFileOrNoOp()

    def contextMenuEvent(self, event):
        menu = _qtw.QMenu()

        load = menu.addAction("Load")
        load.triggered.connect(self._loadFileIntoFolder)

        delete = menu.addAction("Delete")
        delete.triggered.connect(self._deleteCurrentFile)

        menu.exec(event.globalPos())

    def _openCurrentFileOrNoOp(self) -> None:
        path = self._getCurrentPath()
        if not path.is_file():
            return

        try:
            _os.startfile(path)
        except OSError:
            _warn.showMessageBox("Could not open file {path}: no program is associated with its file type.")

    def _loadFileIntoFolder(self) -> None:
        currentPath = self._getCurrentPath()
        targetDirPath = currentPath if currentPath.is_dir() else currentPath.parent

        sourceFilePathString = _qtw.QFileDialog.getOpenFileName(self, "Load file")[0]
        if not sourceFilePathString:
            return

        sourceFilePath = _pl.Path(sourceFilePathString)

        sourceSuffix = sourceFilePath.suffix
        targetSuffix = ".ddck" if sourceSuffix == ".xmltml" else sourceSuffix

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

            if sourceSuffix != ".xmltmf":
                _su.copy(sourceFilePath, targetFilePath)
                return

            self._convertAndLoadProformaFileIntoFolder(sourceFilePath, targetFilePath)

    @staticmethod
    def _convertAndLoadProformaFileIntoFolder(sourceFilePath: _pl.Path, targetFilePath: _pl.Path) -> None:
        sourceFileContent = sourceFilePath.read_text()
        suggestedHydraulicConnections = [_models.Connection(None, _models.InputPort("In"), _models.OutputPort("Out"))]

        maybeCancelled = _pro.convertXmlTmfStringToDdck(
            sourceFileContent,
            suggestedHydraulicConnections,
        )
        if _cancel.isCancelled(maybeCancelled):
            return
        result = _cancel.value(maybeCancelled)
        if _res.isError(result):
            _warn.showMessageBox(_res.error(result).message)
            return
        targetFileContent = _res.value(result)

        assert isinstance(targetFileContent, str)
        targetFilePath.write_text(targetFileContent)

    def _deleteCurrentFile(self) -> None:
        path = self._getCurrentPath()
        if path.is_dir():
            return

        try:
            path.unlink()
        except OSError as error:
            _warn.showMessageBox(f"Could not delete file `{path}`: {error}.")

    def _getCurrentPath(self) -> _pl.Path:
        index = self.currentIndex()
        return self._getPath(index)

    def _getPath(self, index: _qtc.QModelIndex) -> _pl.Path:
        filePathString = self._model.filePath(index)
        return _pl.Path(filePathString)
