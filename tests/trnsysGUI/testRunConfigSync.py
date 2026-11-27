# pylint: disable=invalid-name  # `tmp_path` fixture
import pathlib as _pl

import pytest as _pt

import pytrnsys.trnsys_util.readConfigTrnsys as _rct
import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.active as _active
import trnsysGUI.runConfig.sync as _sync


@_pt.fixture(name="project")
def _project(tmp_path) -> _pl.Path:
    projectDirPath = tmp_path / "myProject"
    for relativePath in [
        "generic/head.ddck",
        "generic/end.ddck",
        "Coll/type1.ddck",
        "Coll/unused.ddck",
        "weather/weather.ddck",
    ]:
        filePath = projectDirPath / "ddck" / relativePath
        filePath.parent.mkdir(parents=True, exist_ok=True)
        filePath.write_text("")
    return projectDirPath


class TestActiveConfig:
    def testListRunConfigs(self, tmp_path):
        for name in [
            "b.config",
            "run.config",
            "process.config",
            "process-cases.config",
            "runLogFile.config",
            "A.config",
        ]:
            (tmp_path / name).write_text("")

        assert _active.listRunConfigs(tmp_path) == [
            "run.config",
            "A.config",
            "b.config",
        ]

    def testActiveConfigDefaultsAndPersistence(self, tmp_path):
        settingsFilePath = tmp_path / "settings" / "activeConfigs.json"
        projectDirPath = tmp_path / "project"
        projectDirPath.mkdir()

        # Nothing there yet: run.config (to be created)
        assert (
            _active.getActiveConfigName(projectDirPath, settingsFilePath)
            == "run.config"
        )

        (projectDirPath / "variant.config").write_text("")
        assert (
            _active.getActiveConfigName(projectDirPath, settingsFilePath)
            == "variant.config"
        )

        (projectDirPath / "run.config").write_text("")
        assert (
            _active.getActiveConfigName(projectDirPath, settingsFilePath)
            == "run.config"
        )

        _active.setActiveConfigName(
            projectDirPath, "variant.config", settingsFilePath
        )
        assert (
            _active.getActiveConfigName(projectDirPath, settingsFilePath)
            == "variant.config"
        )

        # Deleted: falls back
        (projectDirPath / "variant.config").unlink()
        assert (
            _active.getActiveConfigName(projectDirPath, settingsFilePath)
            == "run.config"
        )

    @_pt.mark.parametrize(
        "name, isValid",
        [
            ("variantA", True),
            ("variant-B.config", True),
            ("with space", False),
            ("", False),
            ("process", False),
            ("run", False),  # exists
        ],
    )
    def testCheckNewConfigName(self, tmp_path, name, isValid):
        (tmp_path / "run.config").write_text("")

        errorMessage = _active.checkNewConfigName(tmp_path, name)

        assert (errorMessage is None) == isValid


class TestMinimalConfig:
    def testPytrnsysReadsIt(self, project):
        text = _sync.createMinimalRunConfigText(
            "myProject", "C:/Trnsys18/Exe/TRNExe.exe", "../library"
        )
        (project / "run.config").write_text(text)

        inputs: dict = {}
        lines = _rct.ReadConfigTrnsys().readFile(
            str(project),
            "run.config",
            inputs,
            parseFileCreated=False,
            controlDataType=False,
        )

        assert inputs["nameRef"] == "myProject"
        assert inputs["PROJECT$"] == "ddck"
        assert inputs["COMMON$"] == "../library"
        assert "PROJECT$ generic/head" in [line.strip() for line in lines]

    def testNothingToSyncInNewProject(self, project):
        text = _sync.createMinimalRunConfigText(
            "myProject", "trnsys.exe", None
        )
        config = _rc.RunConfig(text, project / "run.config")
        (project / "ddck" / "Coll" / "unused.ddck").unlink()
        (project / "ddck" / "Coll" / "type1.ddck").unlink()
        (project / "ddck" / "weather" / "weather.ddck").unlink()

        report = _sync.syncConfig(config, project, None)

        assert not report.addedSettings
        assert not report.hasFindings


class TestSync:
    _CONFIG = """\
bool x True
PROJECT$ generic/head
#### component: Coll ####
PROJECT$ Coll/type1
deck CollA 2
#### end component: Coll ####
PROJECT$ missing/file
COMMON$ lib/x as Coll
PROJECT$ generic/end
"""

    def testAddsMissingSettingsAndReports(self, project):
        config = _rc.RunConfig(self._CONFIG, project / "variant.config")

        report = _sync.syncConfig(config, project, None)

        assert report.addedSettings == [
            'string PROJECT$ "ddck"',
            'string nameRef "myProject"',
            'string projectPath "."',
            'string pathToConnectionInfo "DdckPlaceHolderValues.json"',
        ]
        assert [str(p) for p in report.unusedDdckFiles] == [
            "Coll/unused.ddck",
            "weather/weather.ddck",
        ]
        assert [b.line for b in report.brokenIncludes] == [
            "PROJECT$ missing/file",
            "COMMON$ lib/x as Coll",
        ]
        # Nothing removed or changed:
        for line in self._CONFIG.splitlines():
            assert line in config.toText().splitlines()

    def testDefinesLibraryIfUsed(self, project, tmp_path):
        libraryDirPath = tmp_path / "library"
        (libraryDirPath / "lib").mkdir(parents=True)
        (libraryDirPath / "lib" / "x.ddck").write_text("")
        config = _rc.RunConfig(self._CONFIG, project / "run.config")

        report = _sync.syncConfig(config, project, libraryDirPath)

        assert 'string COMMON$ "..\\library"' in report.addedSettings or (
            'string COMMON$ "../library"' in report.addedSettings
        )
        assert [b.line for b in report.brokenIncludes] == [
            "PROJECT$ missing/file"
        ]

    def testAddProjectDdcks(self, project):
        config = _rc.RunConfig(self._CONFIG, project / "run.config")

        _sync.addProjectDdcks(
            config,
            [
                _pl.PurePosixPath("Coll/unused.ddck"),
                _pl.PurePosixPath("weather/weather.ddck"),
            ],
        )

        assert [i.toLine() for i in config.getComponentIncludes("Coll")] == [
            "PROJECT$ Coll/type1",
            "PROJECT$ Coll/unused",
        ]
        lines = config.toText().splitlines()
        assert lines[-2:] == [
            "PROJECT$ weather/weather",
            "PROJECT$ generic/end",
        ]
        report = _sync.syncConfig(config, project, None)
        assert not report.unusedDdckFiles
