import pathlib as _pl
import shutil as _su

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

        assert actualConfigFilePath.read_text() == expectedConfigFilePath.read_text()

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

        assert actualConfigFilePath.read_text() == expectedConfigFilePath.read_text()
