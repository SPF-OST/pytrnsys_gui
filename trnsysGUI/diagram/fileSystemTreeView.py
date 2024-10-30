import os as _os
import pathlib as _pl

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.internalPiping as _ip
import trnsysGUI.loadDdckFile as _ld
import trnsysGUI.warningsAndErrors as _warn


class FileSystemTreeView(_qtw.QTreeView):
    def __init__(
        self,
        rootDirPath: _pl.Path,
        hasInternalPipingsProvider: _ip.HasInternalPipingsProvider,
    ) -> None:
        super().__init__(parent=None)

        self._ddckLoader = _ld.DdckFileLoader(hasInternalPipingsProvider)

        rootFolder = str(rootDirPath)

        self._model = _qtw.QFileSystemModel()
        self._model.setRootPath(rootFolder)

        self.setModel(self._model)

        rootModelIndex = self._model.index(rootFolder)
        self.setRootIndex(rootModelIndex)

    def mouseDoubleClickEvent(  # pylint: disable=unused-argument
        self, event: _qtg.QMouseEvent
    ) -> None:
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
            _warn.showMessageBox(
                "Could not open file {path}: no program is associated with its file type."
            )

    def _loadFileIntoFolder(self) -> None:
        currentPath = self._getCurrentPath()
        targetDirPath = (
            currentPath if currentPath.is_dir() else currentPath.parent
        )
        self._ddckLoader.loadDdckFile(targetDirPath)

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
