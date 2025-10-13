import pathlib as _pl
import shutil as _su

import trnsysGUI as _tg
import trnsysGUI.configFileUpdater as _cfu


class TestConfigFile:
    def testUpdateEmptyConfig(self) -> None:

        dataDirPath = _pl.Path(__file__).parent / "data" / "new"
        actualConfigFilePath = dataDirPath / "input" / "TTES" / "run.config"
        expectedConfigFilePath = dataDirPath / "expected" / "run.config"

        actualConfigFilePath.unlink(missing_ok=True)
        actualConfigFilePath.touch()

        configFile = _cfu.ConfigFileUpdater(actualConfigFilePath)
        configFile.updateConfig()

        assert (
            self._getContentsWithLocalPathsReplaced(actualConfigFilePath)
            == expectedConfigFilePath.read_text()
        )

    def testUpdateExistingConfig(self) -> None:

        dataDirPath = _pl.Path(__file__).parent / "data" / "existing"
        inputConfigFilePath = dataDirPath / "input" / "TTES" / "run.config"
        actualConfigFilePath = dataDirPath / "actual" / "TTES" / "run.config"
        expectedConfigFilePath = dataDirPath / "expected" / "run.config"

        actualContainingDirPath = actualConfigFilePath.parent
        if actualContainingDirPath.exists():
            _su.rmtree(actualContainingDirPath)

        inputContainingDirPath = inputConfigFilePath.parent
        _su.copytree(inputContainingDirPath, actualContainingDirPath)

        actualConfigFilePath.unlink(missing_ok=True)
        actualConfigFilePath.touch()

        configFile = _cfu.ConfigFileUpdater(actualConfigFilePath)
        configFile.updateConfig()

        assert (
            self._getContentsWithLocalPathsReplaced(actualConfigFilePath)
            == expectedConfigFilePath.read_text()
        )

    @staticmethod
    def _getContentsWithLocalPathsReplaced(filePath: _pl.Path) -> str:
        pathToReplace = _pl.Path(_tg.__file__).parents[2]
        replacementPath = r"C:\actions-runner\_work\pytrnsys_gui"
        content = filePath.read_text()
        contentWithPathReplaced = content.replace(
            str(pathToReplace), replacementPath
        )
        return contentWithPathReplaced
