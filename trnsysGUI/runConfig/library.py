"""Locating the default ddck library: `data/ddck` of the pytrnsys_gui
repository (the library referenced as `COMMON$` in run configs). It isn't
part of the installed `trnsysGUI` package.

The configured library path is stored in its own file next to the GUI's
`settings.json` (instead of in `Settings`) on purpose: a new `Settings`
version would make other branches/versions of the GUI fail to start once
this one saved the settings.
"""

import json as _json
import logging as _log
import pathlib as _pl
import typing as _tp

import appdirs as _ad
import trnsysGUI as _tgui

_LOGGER = _log.getLogger("root")

_LIBRARY_RELATIVE_TO_PACKAGE_PARENT = _pl.Path("data") / "ddck"

_SETTINGS_FILE_NAME = "ddckLibrary.json"
_PATH_KEY = "ddckLibraryPath"


def findDefaultDdckLibrary() -> _pl.Path | None:
    """`<pytrnsys_gui checkout>/data/ddck` if the GUI runs from a checkout
    that has it, else None."""
    packageFilePath = _tgui.__file__
    if not packageFilePath:
        return None

    checkoutDirPath = _pl.Path(packageFilePath).parent.parent
    libraryDirPath = checkoutDirPath / _LIBRARY_RELATIVE_TO_PACKAGE_PARENT
    return libraryDirPath if libraryDirPath.is_dir() else None


def getDdckLibraryDirPath(
    configuredPath: str | None = None,
    autoDetect: _tp.Callable[[], _pl.Path | None] = findDefaultDdckLibrary,
) -> _pl.Path | None:
    """The configured library path if it exists, else the auto-detected one,
    else None. Without `configuredPath`, the stored one is used."""
    if configuredPath is None:
        configuredPath = loadConfiguredLibraryPath()

    if configuredPath:
        configuredDirPath = _pl.Path(configuredPath)
        if configuredDirPath.is_dir():
            return configuredDirPath
        _LOGGER.warning(
            "The configured ddck library `%s` doesn't exist: using the"
            " auto-detected one.",
            configuredDirPath,
        )

    return autoDetect()


def loadConfiguredLibraryPath(
    settingsFilePath: _pl.Path | None = None,
) -> str:
    """The configured library path, or "" (meaning: auto-detect)."""
    settingsFilePath = settingsFilePath or _getSettingsFilePath()
    if not settingsFilePath.is_file():
        return ""

    try:
        data = _json.loads(settingsFilePath.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        _LOGGER.warning("Could not read %s: %s", settingsFilePath, error)
        return ""

    value = data.get(_PATH_KEY, "") if isinstance(data, dict) else ""
    return value if isinstance(value, str) else ""


def saveConfiguredLibraryPath(
    path: str, settingsFilePath: _pl.Path | None = None
) -> None:
    """Stores the library path; "" means: auto-detect."""
    settingsFilePath = settingsFilePath or _getSettingsFilePath()
    settingsFilePath.parent.mkdir(parents=True, exist_ok=True)
    settingsFilePath.write_text(
        _json.dumps({_PATH_KEY: path}, indent=4), encoding="utf-8"
    )


def _getSettingsFilePath() -> _pl.Path:
    # Same directory as the GUI's `settings.json`.
    userConfigDirPath = _pl.Path(
        _ad.user_config_dir("pytrnsys-gui", "SPF OST")
    )
    return userConfigDirPath / _SETTINGS_FILE_NAME
