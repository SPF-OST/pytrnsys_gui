__all__ = [
    "CreateProject",
    "LoadProject",
    "MigrateProject",
    "Project",
    "getProject",
    "getExistingEmptyDirectory",
    "getLoadOrMigrateProject",
]

import dataclasses as _dc
import pathlib as _pl
import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.common.cancelled as _ccl
import trnsysGUI.messageBox as mb
from trnsysGUI import constants
from trnsysGUI.dialogs.startupDialog import StartupDialog
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler


@_dc.dataclass
class CreateProject:
    jsonFilePath: _pl.Path


@_dc.dataclass
class LoadProject:
    jsonFilePath: _pl.Path


@_dc.dataclass
class MigrateProject:
    oldJsonFilePath: _pl.Path
    newProjectFolderPath: _pl.Path


Project = CreateProject | LoadProject | MigrateProject


def getProject() -> _ccl.MaybeCancelled[Project]:
    createOpenMaybeCancelled = StartupDialog.showDialogAndGetResult()

    while not _ccl.isCancelled(createOpenMaybeCancelled):
        createOpen = _ccl.value(createOpenMaybeCancelled)

        projectMaybeCancelled = (
            loadRecentProject(createOpen)
            if isinstance(createOpen, _pl.Path)
            else _getProjectInternal(
                constants.CreateNewOrOpenExisting(createOpen)
            )
        )
        if not _ccl.isCancelled(projectMaybeCancelled):
            project = _ccl.value(projectMaybeCancelled)
            assert isinstance(project, (CreateProject, LoadProject))
            RecentProjectsHandler.addProject(project.jsonFilePath)
            return _tp.cast(
                Project, project
            )  # Don't know why mypy requires this cast

        createOpenMaybeCancelled = StartupDialog.showDialogAndGetResult()

    return _ccl.CANCELLED


def _getProjectInternal(
    createOrOpenExisting: "constants.CreateNewOrOpenExisting",
) -> _ccl.MaybeCancelled[Project]:
    if createOrOpenExisting == constants.CreateNewOrOpenExisting.OPEN_EXISTING:
        return getLoadOrMigrateProject()

    if createOrOpenExisting == constants.CreateNewOrOpenExisting.CREATE_NEW:
        return getCreateProject()

    raise AssertionError(
        f"Unknown value for enum {constants.CreateNewOrOpenExisting}: {createOrOpenExisting}"
    )


def getCreateProject(
    startingDirectoryPath: _tp.Optional[_pl.Path] = None,
) -> _ccl.MaybeCancelled[CreateProject]:
    projectFolderPathMaybeCancelled = getExistingEmptyDirectory(
        startingDirectoryPath
    )
    if _ccl.isCancelled(projectFolderPathMaybeCancelled):
        return _ccl.CANCELLED
    projectFolderPath = _ccl.value(projectFolderPathMaybeCancelled)

    jsonFilePath = projectFolderPath / f"{projectFolderPath.name}.json"

    return CreateProject(jsonFilePath)


def getExistingEmptyDirectory(
    startingDirectoryPath: _tp.Optional[_pl.Path] = None,
) -> _ccl.MaybeCancelled[_pl.Path]:
    while True:
        selectedDirectoryPathString = _qtw.QFileDialog.getExistingDirectory(
            caption="Select new project directory",
            directory=str(startingDirectoryPath),
        )
        if not selectedDirectoryPathString:
            return _ccl.CANCELLED

        selectedDirectoryPath = _pl.Path(selectedDirectoryPathString)

        if _isEmptyDirectory(selectedDirectoryPath):
            return selectedDirectoryPath

        mb.MessageBox.create(
            messageText=constants.DIRECTORY_MUST_BE_EMPTY,
            buttons=[_qtw.QMessageBox.Ok],
        )


def _isEmptyDirectory(path: _pl.Path) -> bool:
    if not path.is_dir():
        return False
    containedFilesAndDirectories = list(path.iterdir())
    isDirectoryEmpty = len(containedFilesAndDirectories) == 0
    return isDirectoryEmpty


def getLoadOrMigrateProject() -> (
    _ccl.MaybeCancelled[LoadProject | MigrateProject]
):
    projectFolderPathString, _ = _qtw.QFileDialog.getOpenFileName(
        caption="Open diagram", filter="*.json"
    )
    if not projectFolderPathString:
        return _ccl.CANCELLED
    jsonFilePath = _pl.Path(projectFolderPathString)
    projectFolderPath = jsonFilePath.parent
    return checkIfProjectEnviromentIsValid(projectFolderPath, jsonFilePath)


def loadRecentProject(
    projectPath: _pl.Path,
) -> _ccl.MaybeCancelled[LoadProject | MigrateProject]:
    try:
        if not projectPath.exists():
            if (
                mb.MessageBox.create(
                    messageText=constants.RECENT_MOVED_OR_DELETED,
                    buttons=[_qtw.QMessageBox.Ok],
                )
                == _qtw.QMessageBox.Ok
            ):
                RecentProjectsHandler.removeProject(projectPath)
                return _ccl.CANCELLED
        else:
            return checkIfProjectEnviromentIsValid(
                projectPath.parent, projectPath
            )
    except TypeError:
        if (
            mb.MessageBox.create(
                messageText=constants.NO_RECENT_AVAILABLE,
                buttons=[_qtw.QMessageBox.Ok],
            )
            == _qtw.QMessageBox.Ok
        ):
            return _ccl.CANCELLED
    return _ccl.CANCELLED


def checkIfProjectEnviromentIsValid(
    projectFolderPath, jsonFilePath
) -> _ccl.MaybeCancelled[LoadProject | MigrateProject]:
    containingFolderIsCalledSameAsJsonFile = (
        projectFolderPath.name == jsonFilePath.stem
    )
    ddckFolder = projectFolderPath / "ddck"
    if not containingFolderIsCalledSameAsJsonFile or not ddckFolder.is_dir():
        oldJsonFilePath = jsonFilePath
        if (
            mb.MessageBox.create(
                messageText=constants.NO_PROPER_PROJECT_ENVIRONMENT
            )
            == _qtw.QMessageBox.Cancel
        ):
            return _ccl.CANCELLED
        maybeCancelled = getExistingEmptyDirectory(
            startingDirectoryPath=projectFolderPath.parent
        )
        if _ccl.isCancelled(maybeCancelled):
            return _ccl.CANCELLED
        newProjectFolderPath = _ccl.value(maybeCancelled)
        return MigrateProject(oldJsonFilePath, newProjectFolderPath)
    return LoadProject(jsonFilePath)
