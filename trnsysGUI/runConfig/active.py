"""The active run config of a project: the one the component window edits
and "Run simulation" runs.

The choice is stored per project in the GUI's user config directory (not in
the diagram's JSON, so the diagram format doesn't change).
"""

import json as _json
import logging as _log
import pathlib as _pl
import re as _re
import typing as _tp

import appdirs as _ad

_LOGGER = _log.getLogger("root")

DEFAULT_CONFIG_FILE_NAME = "run.config"
CONFIG_SUFFIX = ".config"

_SETTINGS_FILE_NAME = "activeConfigs.json"

# Configs that aren't run configs: processing configs and the one pytrnsys
# writes itself.
_NON_RUN_CONFIG_REGEX = _re.compile(r"^(process.*|runLogFile)\.config$", _re.I)

_VALID_FILE_STEM_REGEX = _re.compile(r"^[A-Za-z0-9_\-.]+$")


def listRunConfigs(projectDirPath: _pl.Path) -> _tp.Sequence[str]:
    """The run config file names in the project directory, run.config
    first."""
    if not projectDirPath.is_dir():
        return []

    names = [
        p.name
        for p in projectDirPath.glob(f"*{CONFIG_SUFFIX}")
        if p.is_file() and not _NON_RUN_CONFIG_REGEX.match(p.name)
    ]
    return sorted(
        names, key=lambda n: (n != DEFAULT_CONFIG_FILE_NAME, n.lower())
    )


def getActiveConfigName(
    projectDirPath: _pl.Path, settingsFilePath: _pl.Path | None = None
) -> str:
    """The stored choice if that config still exists, else run.config if it
    exists, else the first run config, else "run.config" (to be created)."""
    existingNames = listRunConfigs(projectDirPath)

    storedName = _loadAll(settingsFilePath).get(_getKey(projectDirPath))
    if storedName is not None and storedName in existingNames:
        return storedName

    if DEFAULT_CONFIG_FILE_NAME in existingNames or not existingNames:
        return DEFAULT_CONFIG_FILE_NAME

    return existingNames[0]


def setActiveConfigName(
    projectDirPath: _pl.Path,
    configFileName: str,
    settingsFilePath: _pl.Path | None = None,
) -> None:
    settingsFilePath = settingsFilePath or _getSettingsFilePath()
    allActiveConfigs = _loadAll(settingsFilePath)
    allActiveConfigs[_getKey(projectDirPath)] = configFileName
    settingsFilePath.parent.mkdir(parents=True, exist_ok=True)
    settingsFilePath.write_text(
        _json.dumps(allActiveConfigs, indent=4), encoding="utf-8"
    )


def checkNewConfigName(projectDirPath: _pl.Path, name: str) -> str | None:
    """An error message if `name` (with or without `.config`) can't be
    used for a new run config, else None."""
    fileName = toConfigFileName(name)
    stem = fileName[: -len(CONFIG_SUFFIX)]
    if not stem or not _VALID_FILE_STEM_REGEX.match(stem):
        return (
            "Use only letters, digits, `_`, `-` and `.` for the config's"
            " name."
        )
    if _NON_RUN_CONFIG_REGEX.match(fileName):
        return f"`{fileName}` is reserved for processing or by pytrnsys."
    if (projectDirPath / fileName).exists():
        return f"`{fileName}` already exists."
    return None


def toConfigFileName(name: str) -> str:
    name = name.strip()
    if name.lower().endswith(CONFIG_SUFFIX):
        return name
    return name + CONFIG_SUFFIX


def _getKey(projectDirPath: _pl.Path) -> str:
    try:
        return str(projectDirPath.resolve()).lower()
    except OSError:
        return str(projectDirPath).lower()


def _loadAll(settingsFilePath: _pl.Path | None) -> dict[str, str]:
    settingsFilePath = settingsFilePath or _getSettingsFilePath()
    if not settingsFilePath.is_file():
        return {}
    try:
        data = _json.loads(settingsFilePath.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        _LOGGER.warning("Could not read %s: %s", settingsFilePath, error)
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, str)}


def _getSettingsFilePath() -> _pl.Path:
    # Same directory as the GUI's `settings.json`.
    userConfigDirPath = _pl.Path(
        _ad.user_config_dir("pytrnsys-gui", "SPF OST")
    )
    return userConfigDirPath / _SETTINGS_FILE_NAME
