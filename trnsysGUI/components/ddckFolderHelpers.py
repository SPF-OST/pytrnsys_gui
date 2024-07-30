from __future__ import annotations

import pathlib as _pl
import shutil as _su
import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.internalPiping as _ip
import trnsysGUI.warningsAndErrors as _werrors

if _tp.TYPE_CHECKING:
    import trnsysGUI.BlockItem as _bi


def moveComponentDdckFolderIfNecessary(
    blockItem: _bi.BlockItem, newName: str, oldName: str, projectDirPath: _pl.Path
) -> None:
    if not hasComponentDdckFolder(blockItem):
        return

    oldComponentDirPath = getComponentDdckDirPath(oldName, projectDirPath)

    if oldComponentDirPath.is_dir():
        newComponentDirPath = getComponentDdckDirPath(newName, projectDirPath)
        _su.move(oldComponentDirPath, newComponentDirPath)
    else:
        _werrors.showMessageBox(
            f"The old ddck directory was not found at `{oldComponentDirPath} when trying to rename it to {newName}",
            _werrors.Title.WARNING,
        )
        createComponentDdckFolder(newName, projectDirPath)


def hasComponentDdckFolder(blockItem: _bi.BlockItem) -> bool:
    hasDdckFolder = blockItem.hasDdckDirectory() if isinstance(blockItem, _ip.HasInternalPiping) else False
    return hasDdckFolder


def getComponentDdckDirPath(displayName: str, projectDirPath: _pl.Path) -> _pl.Path:
    oldComponentDirPath = projectDirPath / "ddck" / displayName
    return oldComponentDirPath


def createComponentDdckFolder(name: str, projectDirPath: _pl.Path) -> None:
    newComponentDirPath = getComponentDdckDirPath(name, projectDirPath)
    newComponentDirPath.mkdir()


def maybeDeleteNonEmptyComponentDdckFolder(blockItem: _bi.BlockItem, projectFolder: _pl.Path) -> None:
    if not hasComponentDdckFolder(blockItem):
        return

    displayName = blockItem.displayName

    dirPath = getComponentDdckDirPath(displayName, projectFolder)

    if not dirPath.is_dir():
        return

    childItems = list(dirPath.iterdir())
    if childItems:
        formattedChildItems = "\n".join(p.name for p in childItems)
        message = f"""\
You're about to delete component `{displayName}`. Its component ddck folder is not empty
and contains the following items:

{formattedChildItems}

Would you like to delete the component ddck folder nonetheless? This cannot be undone.
"""
        standardButton = _qtw.QMessageBox.question(None, "Delete component ddck folder?", message)

        if standardButton != _qtw.QMessageBox.StandardButton.Yes:  # pylint: disable=no-member
            return

    _su.rmtree(dirPath)
