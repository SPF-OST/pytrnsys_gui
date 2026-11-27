"""How the active config uses ddck files: for each inclusion of a file, the
component name and the default visibility pytrnsys uses for it."""

import dataclasses as _dc
import pathlib as _pl
import typing as _tp

import pytrnsys.ddck.replaceTokens.defaultVisibility as _dv

from . import importing as _imp
from . import model as _model
from . import sync as _sync

_DEFAULT_VISIBILITY_SETTING = "defaultVisibility"


@_dc.dataclass(frozen=True)
class ConfigContext:
    """The active config and how to resolve its paths."""

    config: _model.RunConfig
    projectDirPath: _pl.Path
    libraryDirPath: _pl.Path | None

    @property
    def configName(self) -> str:
        return self.config.filePath.name if self.config.filePath else "?"

    def getPathVariables(self) -> dict[str, str]:
        variables = _sync.getEffectivePathVariables(
            self.config, self.projectDirPath
        )
        if self.libraryDirPath:
            variables.setdefault(
                _model.LIBRARY_PATH_VARIABLE, str(self.libraryDirPath)
            )
        return variables

    def resolve(self, include: _model.DdckInclude) -> _pl.Path | None:
        return include.resolve(self.getPathVariables(), self.projectDirPath)

    def isLibraryFile(self, filePath: _pl.Path) -> bool:
        return bool(self.libraryDirPath) and _imp.isInDirectory(
            filePath, self.libraryDirPath  # type: ignore[arg-type]
        )


@_dc.dataclass(frozen=True)
class Inclusion:
    """One inclusion of a ddck file in the config."""

    include: _model.DdckInclude
    lineIndex: int
    blockComponentName: str | None
    defaultVisibility: _dv.DefaultVisibility

    @property
    def componentName(self) -> str:
        return self.include.componentName

    @property
    def label(self) -> str:
        visibility = self.defaultVisibility.name.lower()
        name = self.componentName or "(no component)"
        return f"{name} ({visibility}) – {self.include.toLine()}"


def getDefaultVisibility(config: _model.RunConfig) -> _dv.DefaultVisibility:
    """The config's `defaultVisibility` (pytrnsys' default: local)."""
    value = config.getPathVariables().get(_DEFAULT_VISIBILITY_SETTING, "")
    if value.lower() == "global":
        return _dv.DefaultVisibility.GLOBAL
    return _dv.DefaultVisibility.LOCAL


def findInclusions(
    context: ConfigContext, filePath: _pl.Path
) -> _tp.Sequence[Inclusion]:
    """The inclusions of the file in the config, in config order."""
    configVisibility = getDefaultVisibility(context.config)
    targetFilePath = _normalize(filePath)

    inclusions = []
    for includeLine in context.config.getIncludeLines():
        resolvedFilePath = context.resolve(includeLine.include)
        if not resolvedFilePath or _normalize(resolvedFilePath) != (
            targetFilePath
        ):
            continue
        visibility = (
            _dv.DefaultVisibility.GLOBAL
            if includeLine.include.isGlobal
            else configVisibility
        )
        inclusions.append(
            Inclusion(
                includeLine.include,
                includeLine.lineIndex,
                includeLine.blockComponentName,
                visibility,
            )
        )
    return inclusions


def _normalize(filePath: _pl.Path) -> _pl.Path:
    try:
        return filePath.resolve()
    except OSError:
        return filePath
