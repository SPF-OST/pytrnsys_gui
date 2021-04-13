import dataclasses as _dc
import pathlib as _pl
import typing as _tp

import appdirs as _ad
import dataclasses_jsonschema as _dcj


@_dc.dataclass
class Settings(_dcj.JsonSchemaMixin):
    @staticmethod
    def create(trnsysBinaryDirPath: _pl.Path) -> "Settings":
        return Settings(str(trnsysBinaryDirPath))

    _SETTINGS_FILE_NAME = "settings.json"

    trnsysBinaryDirPath: str

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
