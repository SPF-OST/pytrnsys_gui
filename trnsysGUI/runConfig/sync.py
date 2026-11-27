"""Creating a minimal run config and synchronizing a config with the project
without removing anything (replaces the old "Update run.config", which
regenerated all `PROJECT$` lines from the ddck folder).

Relative paths in configs are relative to the project directory: the GUI
runs pytrnsys from there.
"""

import contextlib as _contextlib
import dataclasses as _dc
import os as _os
import pathlib as _pl
import typing as _tp

from . import importing as _imp
from . import model as _model

_DDCK_DIR_NAME = "ddck"
PLACEHOLDER_VALUES_FILE_NAME = "DdckPlaceHolderValues.json"


@_dc.dataclass(frozen=True)
class BrokenInclude:
    line: str
    reason: str


@_dc.dataclass(frozen=True)
class SyncReport:
    addedSettings: _tp.Sequence[str]
    unusedDdckFiles: _tp.Sequence[_pl.PurePosixPath]  # relative to ddck/
    brokenIncludes: _tp.Sequence[BrokenInclude]

    @property
    def hasFindings(self) -> bool:
        return bool(self.unusedDdckFiles or self.brokenIncludes)


def createMinimalRunConfigText(
    projectName: str,
    trnsysExePath: str,
    libraryRelativePath: str | None,
) -> str:
    libraryLine = (
        f'string {_model.LIBRARY_PATH_VARIABLE} "{libraryRelativePath}"\n'
        if libraryRelativePath
        else ""
    )
    return f"""\
############# GENERIC##############################

bool ignoreOnlinePlotter  False
int reduceCpu  1
bool parseFileCreated True
bool runCases True
bool checkDeck True
string outputLevel "INFO"

############# AUTOMATIC WORK BOOL##############################

string defaultVisibility "global"
bool doAutoUnitNumbering True
bool generateUnitTypesUsed True
bool addAutomaticEnergyBalance True

#############PATHS################################

string trnsysExePath "{trnsysExePath}"
string {_model.PROJECT_PATH_VARIABLE} "{_DDCK_DIR_NAME}"
{libraryLine}string projectPath "."
string pathToConnectionInfo "{PLACEHOLDER_VALUES_FILE_NAME}"
string addResultsFolder "results"
string nameRef "{projectName}"
string runType "runFromConfig"

#############FIXED CHANGED IN DDCK##################

deck START 0    # 0 is midnight new year
deck STOP 8760
deck dtSim 1/60    # [h] time step

#############USED DDCKs##################

{_model.PROJECT_PATH_VARIABLE} generic/head
{_model.PROJECT_PATH_VARIABLE} generic/end
"""


def syncConfig(
    config: _model.RunConfig,
    projectDirPath: _pl.Path,
    libraryDirPath: _pl.Path | None,
) -> SyncReport:
    """Adds missing settings (never changes or removes lines) and reports
    ddcks of the project that aren't used and includes that don't resolve.
    """
    addedSettings = _addMissingSettings(config, projectDirPath, libraryDirPath)

    pathVariables = getEffectivePathVariables(config, projectDirPath)
    usedFilePaths: set[_pl.Path] = set()
    brokenIncludes = []
    for includeLine in config.getIncludeLines():
        include = includeLine.include
        lineText = include.toLine()
        filePath = include.resolve(pathVariables, projectDirPath)
        if filePath is None:
            brokenIncludes.append(
                BrokenInclude(
                    lineText, f"{include.pathVariable} is not defined"
                )
            )
        elif not filePath.is_file():
            brokenIncludes.append(
                BrokenInclude(lineText, f"`{filePath}` doesn't exist")
            )
        else:
            usedFilePaths.add(_normalize(filePath))

    ddckDirPath = projectDirPath / _DDCK_DIR_NAME
    unusedDdckFiles = []
    if ddckDirPath.is_dir():
        for filePath in sorted(ddckDirPath.rglob("*.ddck")):
            relativeParts = filePath.relative_to(ddckDirPath).parts
            # Hidden folders, e.g. `.deleted` with deleted components' ddcks
            if any(part.startswith(".") for part in relativeParts):
                continue
            if _normalize(filePath) not in usedFilePaths:
                unusedDdckFiles.append(
                    _pl.PurePosixPath(
                        filePath.relative_to(ddckDirPath).as_posix()
                    )
                )

    return SyncReport(addedSettings, unusedDdckFiles, brokenIncludes)


def addProjectDdcks(
    config: _model.RunConfig,
    relativeDdckFilePaths: _tp.Iterable[_pl.PurePosixPath],
) -> None:
    """Adds `PROJECT$ <folder>/<file>` lines: into the block of the
    component named like the folder if the config has one, else before the
    `end` ddck."""
    componentNames = set(config.getComponentNames())
    for relativePath in relativeDdckFilePaths:
        include = _model.DdckInclude(
            _model.PROJECT_PATH_VARIABLE,
            _imp.toConfigPath(relativePath.with_suffix("")),
        )
        folderName = (
            relativePath.parts[0] if len(relativePath.parts) > 1 else ""
        )
        if folderName in componentNames:
            entries = config.getComponentEntries(folderName)
            config.setComponentEntries(
                folderName, [*entries, _model.ComponentEntry(include)]
            )
        else:
            config.insertIncludeBeforeEnd(include)


def getEffectivePathVariables(
    config: _model.RunConfig, projectDirPath: _pl.Path
) -> dict[str, str]:
    """The config's path variables plus pytrnsys' default for `PROJECT$`."""
    variables = dict(config.getPathVariables())
    variables.setdefault(
        _model.PROJECT_PATH_VARIABLE, str(projectDirPath / _DDCK_DIR_NAME)
    )
    return variables


def _addMissingSettings(
    config: _model.RunConfig,
    projectDirPath: _pl.Path,
    libraryDirPath: _pl.Path | None,
) -> _tp.Sequence[str]:
    variables = config.getPathVariables()
    added = []

    # pytrnsys only defines PROJECT$ itself for files named run.config.
    if _model.PROJECT_PATH_VARIABLE not in variables:
        config.setPathVariable(_model.PROJECT_PATH_VARIABLE, _DDCK_DIR_NAME)
        added.append(
            f'string {_model.PROJECT_PATH_VARIABLE} "{_DDCK_DIR_NAME}"'
        )

    usesLibrary = any(
        il.include.pathVariable == _model.LIBRARY_PATH_VARIABLE
        for il in config.getIncludeLines()
    )
    if (
        usesLibrary
        and _model.LIBRARY_PATH_VARIABLE not in variables
        and libraryDirPath
    ):
        _imp.ensureLibraryPathVariable(config, libraryDirPath)
        value = config.getPathVariables()[_model.LIBRARY_PATH_VARIABLE]
        added.append(f'string {_model.LIBRARY_PATH_VARIABLE} "{value}"')

    # pytrnsys only adds `pathToConnectionInfo` (the placeholder values)
    # itself for files named run.config.
    for name, value in [
        ("nameRef", projectDirPath.name),
        ("projectPath", "."),
        ("pathToConnectionInfo", PLACEHOLDER_VALUES_FILE_NAME),
    ]:
        if name not in variables:
            config.setString(name, value)
            added.append(f'string {name} "{value}"')

    return added


def _normalize(filePath: _pl.Path) -> _pl.Path:
    try:
        return filePath.resolve()
    except OSError:
        return filePath


def loadOrCreateConfig(
    configFilePath: _pl.Path,
    trnsysExePath: str,
    libraryDirPath: _pl.Path | None,
) -> _model.RunConfig:
    """The config, or (if it doesn't exist yet) a minimal one, not written
    until the caller writes it."""
    if configFilePath.is_file():
        return _model.RunConfig.read(configFilePath)

    projectDirPath = configFilePath.parent
    libraryRelativePath = (
        _imp.getRelativePath(libraryDirPath, projectDirPath)
        if libraryDirPath
        else None
    )
    text = createMinimalRunConfigText(
        projectDirPath.name, trnsysExePath, libraryRelativePath
    )
    return _model.RunConfig(text, configFilePath)


@_contextlib.contextmanager
def workingDirectory(dirPath: _pl.Path) -> _tp.Iterator[None]:
    """pytrnsys resolves relative paths in configs against the current
    working directory: run it from the project directory."""
    previousDirPath = _os.getcwd()
    _os.chdir(dirPath)
    try:
        yield
    finally:
        _os.chdir(previousDirPath)
