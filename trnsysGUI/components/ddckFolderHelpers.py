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
    blockItem: _bi.BlockItem,
    newName: str,
    oldName: str,
    projectDirPath: _pl.Path,
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
    hasDdckFolder = (
        blockItem.hasDdckDirectory()
        if isinstance(blockItem, _ip.HasInternalPiping)
        else False
    )
    return hasDdckFolder


def getComponentDdckDirPath(
    displayName: str, projectDirPath: _pl.Path
) -> _pl.Path:
    oldComponentDirPath = projectDirPath / "ddck" / displayName
    return oldComponentDirPath


def createComponentDdckFolder(name: str, projectDirPath: _pl.Path) -> None:
    newComponentDirPath = getComponentDdckDirPath(name, projectDirPath)
    newComponentDirPath.mkdir()


def maybeDeleteNonEmptyComponentDdckFolder(
    blockItem: _bi.BlockItem, projectFolder: _pl.Path
) -> None:
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
        standardButton = _qtw.QMessageBox.question(
            None, "Delete component ddck folder?", message
        )

        if (
            standardButton
            != _qtw.QMessageBox.StandardButton.Yes  # pylint: disable=no-member
        ):
            return

    _su.rmtree(dirPath)


# Deleted components' ddck folders are moved here (instead of being deleted)
# so deleting a component can be undone with its ddck files.
DELETED_DDCK_DIR_NAME = ".deleted"


def isDeletedDdckDir(path: _pl.Path) -> bool:
    return path.name == DELETED_DDCK_DIR_NAME


def moveComponentDdckFolderToTrash(
    blockItem: _bi.BlockItem, projectFolder: _pl.Path
) -> _pl.Path | None:
    """Moves `ddck/<component>` to `ddck/.deleted/<component>` (with a
    number appended if that exists). Returns where it was moved to, or None
    if there was nothing to move."""
    if not hasComponentDdckFolder(blockItem):
        return None

    dirPath = getComponentDdckDirPath(blockItem.displayName, projectFolder)
    if not dirPath.is_dir():
        return None

    trashDirPath = dirPath.parent / DELETED_DDCK_DIR_NAME
    trashDirPath.mkdir(exist_ok=True)

    targetDirPath = trashDirPath / dirPath.name
    number = 2
    while targetDirPath.exists():
        targetDirPath = trashDirPath / f"{dirPath.name}_{number}"
        number += 1

    _su.move(str(dirPath), str(targetDirPath))
    return targetDirPath


def restoreComponentDdckFolderFromTrash(
    trashedDirPath: _pl.Path, displayName: str, projectFolder: _pl.Path
) -> bool:
    """Moves a folder moved to the trash by `moveComponentDdckFolderToTrash`
    back to `ddck/<displayName>`. False if that's not possible (the trashed
    folder is gone or the target exists and isn't empty)."""
    if not trashedDirPath.is_dir():
        return False

    targetDirPath = getComponentDdckDirPath(displayName, projectFolder)
    if targetDirPath.exists():
        if not targetDirPath.is_dir() or any(targetDirPath.iterdir()):
            return False
        targetDirPath.rmdir()

    _su.move(str(trashedDirPath), str(targetDirPath))

    trashDirPath = trashedDirPath.parent
    if trashDirPath.is_dir() and not any(trashDirPath.iterdir()):
        trashDirPath.rmdir()
    return True
