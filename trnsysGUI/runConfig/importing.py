"""Importing ddcks of the library into a project: as a local copy (with the
data files it `ASSIGN`s) or as a reference to the original.

pytrnsys replaces `PATH$` in `ASSIGN` statements with the root of the path
variable through which the ddck is included (`buildTrnsysDeck`): for a
library ddck included via `COMMON$` that's the library, for a copy included
via `PROJECT$` it's the project's `ddck` folder. Hence the `ASSIGN`s of a
copy must be rewritten to point to the copied data files.
"""

import dataclasses as _dc
import os as _os
import pathlib as _pl
import re as _re
import shutil as _su
import typing as _tp

from . import model as _model

_ASSIGN_REGEX = _re.compile(
    r'^(?P<prefix>\s*ASSIGN\s+"?)(?P<path>[^"\s]+)', _re.IGNORECASE
)
_PATH_KEY = "path$"

_DDCK_SUFFIX = ".ddck"


class DdckImportError(Exception):
    pass


class TargetFilesExistError(Exception):
    def __init__(self, filePaths: _tp.Sequence[_pl.Path]) -> None:
        super().__init__(
            "The following files already exist: "
            + ", ".join(str(p) for p in filePaths)
        )
        self.filePaths = list(filePaths)


@_dc.dataclass(frozen=True)
class CopyResult:
    include: _model.DdckInclude
    copiedFilePaths: _tp.Sequence[_pl.Path]
    warnings: _tp.Sequence[str]


@_dc.dataclass(frozen=True)
class _DataFile:
    lineIndex: int
    sourceFilePath: _pl.Path
    relativeToDdckDir: _pl.PurePath


def toConfigPath(path: _pl.PurePath) -> str:
    """Paths in include lines use `/` (as in existing project configs)."""
    return path.as_posix()


def createLibraryReference(
    libraryDirPath: _pl.Path,
    libraryDdckFilePath: _pl.Path,
    componentName: str | None,
    alias: str | None = None,
) -> _model.DdckInclude:
    """`COMMON$ <path in library> as <alias or component name>`. For a
    component the `as` is always written: without it pytrnsys would use the
    name of the ddck's directory in the library as component name. Without
    a component (project ddcks), there's no `as` unless an alias is given."""
    relativePath = _getRelativePathWithoutSuffix(
        libraryDirPath, libraryDdckFilePath
    )
    return _model.DdckInclude(
        _model.LIBRARY_PATH_VARIABLE,
        toConfigPath(relativePath),
        alias=alias or componentName,
    )


@_dc.dataclass(frozen=True)
class CopyPlan:
    """What `copyIntoProject` would do, without doing it."""

    libraryDirPath: _pl.Path
    libraryDdckFilePath: _pl.Path
    componentName: str
    include: _model.DdckInclude
    targetDdckFilePath: _pl.Path
    targetDataFilePaths: _tp.Sequence[_pl.Path]
    warnings: _tp.Sequence[str]

    @property
    def targetFilePaths(self) -> _tp.Sequence[_pl.Path]:
        return [self.targetDdckFilePath, *self.targetDataFilePaths]

    def getExistingTargetFilePaths(self) -> _tp.Sequence[_pl.Path]:
        return [p for p in self.targetFilePaths if p.exists()]


def planCopy(
    libraryDirPath: _pl.Path,
    libraryDdckFilePath: _pl.Path,
    projectDdckDirPath: _pl.Path,
    componentName: str,
    alias: str | None = None,
) -> CopyPlan:
    """See `copyIntoProject`."""
    if libraryDdckFilePath.suffix.lower() != _DDCK_SUFFIX:
        raise DdckImportError(
            f"`{libraryDdckFilePath.name}` is not a ddck file."
        )

    lines = _readText(libraryDdckFilePath).text.split("\n")
    dataFiles, warnings = _findDataFiles(
        lines, libraryDirPath, libraryDdckFilePath.parent
    )

    targetDirPath = projectDdckDirPath / componentName
    relativePath = _pl.PurePosixPath(componentName, libraryDdckFilePath.stem)
    # Without `as`, pytrnsys uses the containing directory, i.e. the
    # component's name.
    include = _model.DdckInclude(
        _model.PROJECT_PATH_VARIABLE,
        toConfigPath(relativePath),
        alias=alias if alias and alias != componentName else None,
    )

    return CopyPlan(
        libraryDirPath,
        libraryDdckFilePath,
        componentName,
        include,
        targetDirPath / libraryDdckFilePath.name,
        [targetDirPath / df.relativeToDdckDir for df in dataFiles],
        warnings,
    )


def copyIntoProject(  # pylint: disable=too-many-arguments
    libraryDirPath: _pl.Path,
    libraryDdckFilePath: _pl.Path,
    projectDdckDirPath: _pl.Path,
    componentName: str,
    *,
    alias: str | None = None,
    overwrite: bool = False,
) -> CopyResult:
    """Copies the ddck to `<project ddck dir>/<component>/` together with the
    data files it `ASSIGN`s via `PATH$`, and rewrites those `ASSIGN`s. Data
    files next to (or below) the ddck keep their place relative to it, others
    (e.g. shared profiles) their place in the library. Raises
    `TargetFilesExistError` if files would be overwritten and `overwrite` is
    False."""
    plan = planCopy(
        libraryDirPath,
        libraryDdckFilePath,
        projectDdckDirPath,
        componentName,
        alias,
    )
    return executeCopy(plan, overwrite)


def executeCopy(plan: CopyPlan, overwrite: bool = False) -> CopyResult:
    existingFilePaths = plan.getExistingTargetFilePaths()
    if existingFilePaths and not overwrite:
        raise TargetFilesExistError(existingFilePaths)

    content = _readText(plan.libraryDdckFilePath)
    lines = content.text.split("\n")
    dataFiles, _ = _findDataFiles(
        lines, plan.libraryDirPath, plan.libraryDdckFilePath.parent
    )

    for dataFile in dataFiles:
        match = _ASSIGN_REGEX.match(lines[dataFile.lineIndex])
        assert match
        newPath = "\\".join(
            ["PATH$", plan.componentName, *dataFile.relativeToDdckDir.parts]
        )
        lines[dataFile.lineIndex] = (
            match.group("prefix")
            + newPath
            + lines[dataFile.lineIndex][match.end("path") :]
        )

    plan.targetDdckFilePath.parent.mkdir(parents=True, exist_ok=True)
    _writeText(
        plan.targetDdckFilePath, _dc.replace(content, text="\n".join(lines))
    )
    for dataFile, targetFilePath in zip(dataFiles, plan.targetDataFilePaths):
        targetFilePath.parent.mkdir(parents=True, exist_ok=True)
        _su.copyfile(dataFile.sourceFilePath, targetFilePath)

    return CopyResult(plan.include, plan.targetFilePaths, plan.warnings)


def ensureLibraryPathVariable(
    config: _model.RunConfig, libraryDirPath: _pl.Path
) -> str | None:
    """Defines `COMMON$` as the library (relative to the config's directory
    if possible). Returns a warning if the config already defines it as a
    different directory (which is then left as it is)."""
    variableName = _model.LIBRARY_PATH_VARIABLE
    existingValue = config.getPathVariables().get(variableName)

    if existingValue is not None:
        existingDirPath = _pl.Path(existingValue)
        if not existingDirPath.is_absolute():
            existingDirPath = config.configDirPath / existingDirPath
        if _isSameDirectory(existingDirPath, libraryDirPath):
            return None
        return (
            f"The config defines {variableName} as `{existingValue}`, which"
            f" is not the ddck library `{libraryDirPath}`: the reference will"
            f" point into `{existingDirPath}`."
        )

    config.setPathVariable(
        variableName, _getConfigRelativePath(config, libraryDirPath)
    )
    return None


def isInDirectory(filePath: _pl.Path, dirPath: _pl.Path) -> bool:
    try:
        filePath.resolve().relative_to(dirPath.resolve())
    except ValueError:
        return False
    return True


def _findDataFiles(
    lines: _tp.Sequence[str],
    libraryDirPath: _pl.Path,
    ddckDirPath: _pl.Path,
) -> _tp.Tuple[_tp.Sequence[_DataFile], _tp.Sequence[str]]:
    dataFiles = []
    warnings = []
    for lineIndex, line in enumerate(lines):
        if line.lstrip().startswith("*"):
            continue
        match = _ASSIGN_REGEX.match(line)
        if not match:
            continue

        assignedPath = match.group("path")
        parts = _pl.PureWindowsPath(assignedPath).parts
        if not parts or parts[0].lower() != _PATH_KEY:
            continue  # absolute or other: stays valid after copying

        sourceFilePath = libraryDirPath.joinpath(*parts[1:])
        if not sourceFilePath.is_file():
            warnings.append(
                f"Line {lineIndex + 1}: `{assignedPath}` doesn't exist in the"
                " library: it was not copied."
            )
            continue

        # Files next to (or below) the ddck keep their place relative to
        # it, others (e.g. shared profiles) their place in the library.
        baseDirPath = (
            ddckDirPath
            if isInDirectory(sourceFilePath, ddckDirPath)
            else libraryDirPath
        )
        relativePath = sourceFilePath.resolve().relative_to(
            baseDirPath.resolve()
        )
        dataFiles.append(_DataFile(lineIndex, sourceFilePath, relativePath))

    return dataFiles, warnings


def _getRelativePathWithoutSuffix(
    dirPath: _pl.Path, filePath: _pl.Path
) -> _pl.PurePath:
    if not isInDirectory(filePath, dirPath):
        raise DdckImportError(
            f"`{filePath}` is not in the library `{dirPath}`."
        )
    relativePath = filePath.resolve().relative_to(dirPath.resolve())
    return relativePath.with_suffix("")


def _getConfigRelativePath(config: _model.RunConfig, dirPath: _pl.Path) -> str:
    return getRelativePath(dirPath, config.configDirPath)


def getRelativePath(dirPath: _pl.Path, startDirPath: _pl.Path) -> str:
    """`dirPath` relative to `startDirPath` if possible (else absolute)."""
    try:
        return _os.path.relpath(dirPath, startDirPath)
    except ValueError:  # e.g. different drives on Windows
        return str(dirPath)


def _isSameDirectory(first: _pl.Path, second: _pl.Path) -> bool:
    try:
        return first.resolve() == second.resolve()
    except OSError:
        return False


@_dc.dataclass(frozen=True)
class _TextContent:
    text: str  # with "\n" line endings
    encoding: str
    newline: str


def _readText(filePath: _pl.Path) -> _TextContent:
    data = filePath.read_bytes()
    try:
        text = data.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = data.decode("windows-1252")
        encoding = "windows-1252"
    newline = "\r\n" if "\r\n" in text else "\n"
    return _TextContent(text.replace("\r\n", "\n"), encoding, newline)


def _writeText(filePath: _pl.Path, content: _TextContent) -> None:
    data = content.text.replace("\n", content.newline).encode(content.encoding)
    filePath.write_bytes(data)
