import itertools as _it
import logging as _log
import pathlib as _pl
import typing as _tp
import unittest.mock as _mock

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import pytrnsys.utils.result as _res

import trnsysGUI.BlockItem as _bi
import trnsysGUI.deleteBlockCommand as _dbc
import trnsysGUI.names.manager as _nm
import trnsysGUI.names.undo as _nu
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.PV import PV  # type: ignore[attr-defined]


class TestDeleteBlockCommand:
    @_pt.mark.parametrize(
        "blockItemClass, trnsysType, hasDdckFolder",
        [(PV, "PV", False), (GenericBlock, "GenericBlock", True)],
    )
    def testDeleteUndoRedo(  # pylint: disable=too-many-positional-arguments
        self,
        blockItemClass: type[_bi.BlockItem],
        trnsysType: str,
        hasDdckFolder: bool,
        qtbot,
        tmp_path: _pl.Path,  # pylint: disable=invalid-name  # NOSONAR
    ) -> None:
        editorMock = self._createEditorMock(qtbot, tmp_path)

        displayName = "Blk"
        blockItem = blockItemClass(trnsysType, editorMock, displayName)
        editorMock.trnsysObj.append(blockItem)
        editorMock.diagramScene.addItem(blockItem)

        namesManager = _nm.NamesManager(
            [displayName], _nm.DdckDirFileOrDirNamesProvider(tmp_path / "ddck")
        )
        componentDdckDirPath = tmp_path / "ddck" / displayName
        if hasDdckFolder:
            componentDdckDirPath.mkdir()

        undoStack = _qtw.QUndoStack(editorMock)
        command = _dbc.DeleteBlockCommand(
            blockItem,
            editorMock,
            _nu.UndoNamingHelper.create(namesManager),
        )

        undoStack.push(command)
        self._assertIsDeleted(blockItem, editorMock, namesManager)
        assert not componentDdckDirPath.exists()

        undoStack.undo()
        assert blockItem.displayName == displayName
        assert editorMock.trnsysObj == [blockItem]
        assert blockItem.scene() is editorMock.diagramScene
        assert self._isNameTaken(displayName, namesManager)

        undoStack.redo()
        self._assertIsDeleted(blockItem, editorMock, namesManager)

    @classmethod
    def _assertIsDeleted(
        cls,
        blockItem: _bi.BlockItem,
        editorMock: _tp.Any,
        namesManager: _nm.NamesManager,
    ) -> None:
        assert editorMock.trnsysObj == []
        assert blockItem.scene() is None
        assert not cls._isNameTaken(blockItem.displayName, namesManager)

    @staticmethod
    def _isNameTaken(name: str, namesManager: _nm.NamesManager) -> bool:
        result = namesManager.validateName(name, checkDdckFolder=False)
        return _res.isError(result)

    @staticmethod
    def _createEditorMock(qtbot, projectFolderPath: _pl.Path) -> _tp.Any:
        editorMock: _tp.Any = _qtw.QWidget()
        qtbot.addWidget(editorMock)

        editorMock.logger = _log.getLogger("root")
        editorMock.trnsysObj = []
        editorMock.moveDirectPorts = True
        editorMock.snapGrid = False
        editorMock.alignMode = False

        (projectFolderPath / "ddck").mkdir()
        editorMock.projectFolder = str(projectFolderPath)

        ids = _it.count(7701)
        editorMock.idGen = _mock.Mock(
            name="idGen", spec_set=["getID", "getTrnsysID"]
        )
        editorMock.idGen.getID = lambda: next(ids)
        editorMock.idGen.getTrnsysID = lambda: next(ids)

        editorMock.diagramScene = _qtw.QGraphicsScene(parent=editorMock)

        return editorMock
