# pylint: skip-file
# type: ignore

import dataclasses as _dc
import pathlib as _pl
import typing as _tp
import uuid as _uuid

import appdirs as _ad

import trnsysGUI.serialization as _ser


@_dc.dataclass
class SettingsVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('f7a2c37c-ce82-4a4a-9869-80f00083275b')

    trnsysBinaryDirPath: str


@_dc.dataclass
class Settings(_ser.UpgradableJsonSchemaMixin):
    @staticmethod
    def create(trnsysBinaryDirPath: _pl.Path) -> "Settings":
        return Settings(str(trnsysBinaryDirPath))

    _SETTINGS_FILE_NAME = "settings.json"

    trnsysBinaryPath: str

    @classmethod
    def tryLoadOrNone(cls) -> _tp.Optional["Settings"]:
        settingsFilePath = cls._getSettingsFilePath()

        if not settingsFilePath.exists():
            return None

        data = settingsFilePath.read_text()

        return Settings.from_json(data)

    @classmethod
    def load(cls) -> "Settings":
        settings = cls.tryLoadOrNone()

        if not settings:
            raise RuntimeError("No settings found.")

        return settings

    def save(self) -> None:
        settingsFilePath = self._getSettingsFilePath()

        settingsDirPath = settingsFilePath.parent
        if not settingsDirPath.exists():
            settingsDirPath.mkdir(parents=True)

        data = self.to_json(indent=4)
        settingsFilePath.write_text(data)

    @classmethod
    def _getSettingsFilePath(cls) -> _pl.Path:
        userConfigDirPath = _pl.Path(_ad.user_config_dir("pytrnsys-gui", "SPF OST"))
        settingsFilePath = userConfigDirPath / cls._SETTINGS_FILE_NAME
        return settingsFilePath

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[SettingsVersion0]:
        return SettingsVersion0

    @classmethod
    def upgrade(cls, superseded: SettingsVersion0) -> "Settings":
        trnsysBinaryPath = _pl.Path(superseded.trnsysBinaryDirPath) / "TRNExe.exe"
        return Settings.create(trnsysBinaryPath)

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('e5ea1fbd-1be9-4415-b3e9-7f3a2a11d216')
