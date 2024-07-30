import pathlib as _pl
import typing as _tp

from PyQt5 import QtWidgets as _qtw

import trnsysGUI.BlockItem as _bi
import trnsysGUI.internalPiping as _ip
import trnsysGUI.loadDdckFile as _ld


class BlockItemHasInternalPiping(_bi.BlockItem, _ip.HasInternalPiping):
    @_tp.override
    def getDisplayName(self) -> str:
        raise NotImplementedError()

    def getInternalPiping(self) -> _ip.InternalPiping:
        raise NotImplementedError()

    @_tp.override
    def _addChildContextMenuActions(self, contextMenu: _qtw.QMenu) -> None:
        if self.hasDdckDirectory():
            loadDdckAction = contextMenu.addAction("Load ddck file...")
            loadDdckAction.triggered.connect(self._onLoadDdckActionTriggered)

    def _onLoadDdckActionTriggered(self) -> None:
        ddckFileLoader = _ld.DdckFileLoader(self.editor)

        projectDirPath = _pl.Path(self.editor.projectFolder)
        targetDirPath = projectDirPath / "ddck" / self.displayName

        ddckFileLoader.loadDdckFile(targetDirPath)
