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
import enum as _enum
import pathlib as _pl
import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.common.cancelled as _ccl
from trnsysGUI.UserSettings import UserSettings

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
    createOpenMaybeCancelled = _askUserWhetherToCreateNewProjectOrOpenExisting()

    while not _ccl.isCancelled(createOpenMaybeCancelled):
        createOpen = _ccl.value(createOpenMaybeCancelled)

        projectMaybeCancelled = _getProjectInternal(createOpen)
        if not _ccl.isCancelled(projectMaybeCancelled):
            project = _ccl.value(projectMaybeCancelled)
            return _tp.cast(Project, project)  # Don't know why mypy requires this cast

        createOpenMaybeCancelled = _askUserWhetherToCreateNewProjectOrOpenExisting()

    return _ccl.CANCELLED

class _CreateNewOrOpenExisting(_enum.Enum):
    CREATE_NEW = _enum.auto()
    OPEN_EXISTING = _enum.auto()
    OPEN_RECENT = _enum.auto()

def _askUserWhetherToCreateNewProjectOrOpenExisting() -> _ccl.MaybeCancelled[_CreateNewOrOpenExisting]:
    messageBox = _qtw.QMessageBox()
    messageBox.setWindowTitle("Start a new or open an existing project")
    messageBox.setText("Do you want to start a new project or open an existing one?")
    recentButton = _qtw.QPushButton("Recent")
    createButton = _qtw.QPushButton("New")
    openButton = _qtw.QPushButton("Open")
    messageBox.addButton(createButton, _qtw.QMessageBox.YesRole)
    messageBox.addButton(openButton, _qtw.QMessageBox.NoRole)
    messageBox.addButton(recentButton, _qtw.QMessageBox.NoRole)
    messageBox.addButton(_qtw.QMessageBox.Cancel)
    messageBox.setFocus()
    messageBox.exec()

    clickedButton = messageBox.clickedButton()

    cancelButton = messageBox.button(_qtw.QMessageBox.Cancel)
    if clickedButton is cancelButton:
        return _ccl.CANCELLED

    if clickedButton is createButton:
        return _CreateNewOrOpenExisting.CREATE_NEW

    if clickedButton is openButton:
        return _CreateNewOrOpenExisting.OPEN_EXISTING

    if clickedButton is recentButton:
        return _CreateNewOrOpenExisting.OPEN_RECENT

    raise AssertionError("Unknown button was clicked.")


def _getProjectInternal(createOrOpenExisting: "_CreateNewOrOpenExisting") -> _ccl.MaybeCancelled[Project]:
    if createOrOpenExisting == _CreateNewOrOpenExisting.OPEN_EXISTING:
        return getLoadOrMigrateProject()

    if createOrOpenExisting == _CreateNewOrOpenExisting.CREATE_NEW:
        return getCreateProject()

    if createOrOpenExisting == _CreateNewOrOpenExisting.OPEN_RECENT:
        return loadRecentProject()

    raise AssertionError(f"Unknown value for enum {_CreateNewOrOpenExisting}: {createOrOpenExisting}")


def getCreateProject(startingDirectoryPath: _tp.Optional[_pl.Path] = None) -> _ccl.MaybeCancelled[CreateProject]:
    projectFolderPathMaybeCancelled = getExistingEmptyDirectory(startingDirectoryPath)
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
            caption="Select new project directory", directory=str(startingDirectoryPath)
        )
        if not selectedDirectoryPathString:
            return _ccl.CANCELLED

        selectedDirectoryPath = _pl.Path(selectedDirectoryPathString)

        if _isEmptyDirectory(selectedDirectoryPath):
            return selectedDirectoryPath

        errorMessage = "The new project directory must be empty."

        messageBox = _qtw.QMessageBox()
        messageBox.setText(errorMessage)
        messageBox.exec()

def _isEmptyDirectory(path: _pl.Path) -> bool:
    if not path.is_dir():
        return False
    containedFilesAndDirectories = list(path.iterdir())
    isDirectoryEmpty = len(containedFilesAndDirectories) == 0
    return isDirectoryEmpty

def getLoadOrMigrateProject() -> _ccl.MaybeCancelled[LoadProject | MigrateProject]:
    projectFolderPathString, _ = _qtw.QFileDialog.getOpenFileName(caption="Open diagram", filter="*.json")
    if not projectFolderPathString:
        return _ccl.CANCELLED
    jsonFilePath = _pl.Path(projectFolderPathString)
    projectFolderPath = jsonFilePath.parent
    return checkIfProjectEnviromentIsValid(projectFolderPath, jsonFilePath)

def loadRecentProject()-> _ccl.MaybeCancelled[LoadProject]:
    messageBox = _qtw.QMessageBox()
    messageBox.setStandardButtons(_qtw.QMessageBox.Ok)
    try:
        recentProjectJsonPath = _pl.Path(UserSettings.getRecentProjectJsonPath())
        if not recentProjectJsonPath.exists():
            messageBox.setText("Recent project has moved or was deleted")
            result = messageBox.exec()
            if result == _qtw.QMessageBox.Ok:
                return _ccl.CANCELLED
        else:
            return checkIfProjectEnviromentIsValid(recentProjectJsonPath.parent, recentProjectJsonPath)
    except:
        messageBox.setText("No recent project available")
        result = messageBox.exec()
        if result == _qtw.QMessageBox.Ok:
            return _ccl.CANCELLED

def checkIfProjectEnviromentIsValid(projectFolderPath, jsonFilePath) -> _ccl.MaybeCancelled[LoadProject | MigrateProject]:
    containingFolderIsCalledSameAsJsonFile = projectFolderPath.name == jsonFilePath.stem
    ddckFolder = projectFolderPath / "ddck"
    if not containingFolderIsCalledSameAsJsonFile or not ddckFolder.is_dir():
        oldJsonFilePath = jsonFilePath
        messageBox = _qtw.QMessageBox()
        messageBox.setText(
            "The json you are opening does not have a proper project folder environment. "
            "Do you want to continue and create one?"
        )
        messageBox.setStandardButtons(_qtw.QMessageBox.Yes | _qtw.QMessageBox.Cancel)
        messageBox.setDefaultButton(_qtw.QMessageBox.Cancel)
        result = messageBox.exec()
        if result == _qtw.QMessageBox.Cancel:
            return _ccl.CANCELLED
        maybeCancelled = getExistingEmptyDirectory(startingDirectoryPath=projectFolderPath.parent)
        if _ccl.isCancelled(maybeCancelled):
            return _ccl.CANCELLED
        newProjectFolderPath = _ccl.value(maybeCancelled)
        return MigrateProject(oldJsonFilePath, newProjectFolderPath)
    return LoadProject(jsonFilePath)
