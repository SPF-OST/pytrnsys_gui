# pylint: disable=invalid-name  # `tmp_path` fixture
# pylint: disable=protected-access
import pathlib as _pl

import pytest as _pt
import PyQt5.QtWidgets as _qtw

import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.active as _active
import trnsysGUI.runConfig.controller as _ctrl
import trnsysGUI.runConfig.library as _library


@_pt.fixture(name="project")
def _project(tmp_path, monkeypatch) -> _pl.Path:
    # Don't touch the user's settings.
    monkeypatch.setattr(
        _active,
        "_getSettingsFilePath",
        lambda: tmp_path / "settings" / "activeConfigs.json",
    )
    monkeypatch.setattr(
        _library, "getDdckLibraryDirPath", lambda *_, **__: None
    )

    projectDirPath = tmp_path / "myProject"
    for relativePath in ["generic/head.ddck", "generic/end.ddck"]:
        filePath = projectDirPath / "ddck" / relativePath
        filePath.parent.mkdir(parents=True, exist_ok=True)
        filePath.write_text("")
    return projectDirPath


@_pt.fixture(name="controller")
def _controller(project, qtbot) -> _ctrl.RunConfigController:
    widget = _qtw.QWidget()
    qtbot.addWidget(widget)
    controller = _ctrl.RunConfigController(
        widget, lambda: project, lambda: "C:/Trnsys18/Exe/TRNExe.exe"
    )
    controller.refresh()
    return controller


def _getComboBoxItems(controller):
    comboBox = controller.comboBox
    return [comboBox.itemText(i) for i in range(comboBox.count())]


class TestRunConfigController:
    def testNewProjectShowsRunConfigToBeCreated(self, controller, project):
        assert _getComboBoxItems(controller) == ["run.config (new)"]
        assert controller.activeConfigFilePath == project / "run.config"

    def testPrepareForRunCreatesMinimalConfig(self, controller, project):
        assert controller.prepareForRun()

        config = _rc.RunConfig.read(project / "run.config")
        assert config.getPathVariables()["nameRef"] == "myProject"
        assert [il.include.toLine() for il in config.getIncludeLines()] == [
            "PROJECT$ generic/head",
            "PROJECT$ generic/end",
        ]
        assert _getComboBoxItems(controller) == ["run.config"]

    def testPrepareForRunAsksIfDdcksAreMissing(
        self, controller, project, monkeypatch
    ):
        (project / "run.config").write_text("PROJECT$ missing/file\n")
        questions = []
        monkeypatch.setattr(
            _qtw.QMessageBox,
            "question",
            lambda *args: questions.append(args[2]) or _qtw.QMessageBox.No,
        )

        assert not controller.prepareForRun()
        assert "missing/file" in questions[0]

    def testExportCreatesVariantAndActivatesIt(self, controller, project):
        (project / "run.config").write_text(
            'string nameRef "myProject"\nPROJECT$ generic/head\n'
        )

        newConfigFilePath = controller.exportActiveConfigAs("variantA")

        assert newConfigFilePath == project / "variantA.config"
        assert controller.activeConfigFileName == "variantA.config"
        variables = _rc.RunConfig.read(newConfigFilePath).getPathVariables()
        # Results don't overwrite the original's; PROJECT$ is explicit since
        # pytrnsys only defines it for run.config.
        assert variables["nameRef"] == "variantA"
        assert variables["PROJECT$"] == "ddck"
        # The original is unchanged.
        assert (project / "run.config").read_text() == (
            'string nameRef "myProject"\nPROJECT$ generic/head\n'
        )

    def testExportAsksForValidName(self, controller, project, monkeypatch):
        (project / "run.config").write_text("")
        answers = iter([("bad name", True), ("good", True)])
        prompts = []

        def getText(*args, **_kwargs):
            prompts.append(args[2])
            return next(answers)

        monkeypatch.setattr(_qtw.QInputDialog, "getText", getText)
        monkeypatch.setattr(
            _qtw.QMessageBox, "information", lambda *_: _qtw.QMessageBox.Ok
        )

        controller.exportConfig()

        assert len(prompts) == 2
        assert "letters, digits" in prompts[1]
        assert (project / "good.config").is_file()
        assert _getComboBoxItems(controller) == ["run.config", "good.config"]

    def testChoosingConfigInComboBoxActivatesIt(self, controller, project):
        (project / "run.config").write_text("")
        (project / "other.config").write_text("")
        controller.refresh()

        controller.comboBox.activated.emit(1)

        assert controller.activeConfigFileName == "other.config"
