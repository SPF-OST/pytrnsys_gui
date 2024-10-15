import pathlib as _pl
from PyQt5.QtCore import QSettings  # pylint: disable=invalid-name


class UserSettings:

    _SETTINGS = QSettings("SPF", "pytrnsys")

    @staticmethod
    def setRecentProjectJsonPath(jsonFilePath: _pl.Path) -> None:
        jsonFilePath = _pl.Path(jsonFilePath)
        if jsonFilePath.exists():
            UserSettings._SETTINGS.setValue("recentProject", jsonFilePath)

    @staticmethod
    def getRecentProjectJsonPath() -> _pl.Path:
        return UserSettings._SETTINGS.value("recentProject")
