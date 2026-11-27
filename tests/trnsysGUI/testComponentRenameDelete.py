# pylint: disable=protected-access
# pylint: disable=invalid-name  # `tmp_path` fixture
import pathlib as _pl
import shutil as _sh

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import pytrnsys.utils.log as _ulog
import trnsysGUI.componentWindow.prefixedIdentifiersDialog as _pid
import trnsysGUI.componentWindow.window as _cw
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj
import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.sync as _sync

_EXAMPLE_DIR_PATH = (
    _pl.Path(__file__).parents[2] / "data" / "examples" / "solar_dhw_GUI"
)

_RUN_CONFIG = """\
string PROJECT$ "ddck"
deck CollectorArea 12
PROJECT$ generic/head
#### component: Collector ####
PROJECT$ Collector/type1
deck CollectorNbModTot 360
#### end component: Collector ####
PROJECT$ generic/end
"""


@_pt.fixture(name="mainWindow")
def _mainWindow(tmp_path, qtbot, monkeypatch) -> _mw.MainWindow:
    projectDirPath = tmp_path / "solar_dhw_GUI"
    for relativePath in [
        "Collector/type1.ddck",
        "generic/head.ddck",
        "generic/end.ddck",
    ]:
        filePath = projectDirPath / "ddck" / relativePath
        filePath.parent.mkdir(parents=True, exist_ok=True)
        filePath.write_text("")
    _sh.copy(_EXAMPLE_DIR_PATH / "solar_dhw_GUI.json", projectDirPath)
    (projectDirPath / "run.config").write_text(_RUN_CONFIG)

    monkeypatch.setattr(
        _qtw.QMessageBox, "warning", lambda *_, **__: _qtw.QMessageBox.Ok
    )

    logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")
    project = _prj.LoadProject(projectDirPath / "solar_dhw_GUI.json")
    mainWindow = _mw.MainWindow(logger, project)
    mainWindow.showBoxOnClose = False
    qtbot.addWidget(mainWindow)
    return mainWindow


def _getCollector(mainWindow):
    return next(
        o
        for o in mainWindow.editor.trnsysObj
        if getattr(o, "displayName", None) == "Collector"
    )


class TestDeleteAndUndo:
    def testDdckFolderGoesToTrashAndBack(self, mainWindow):
        projectDirPath = _pl.Path(mainWindow.editor.projectFolder)
        ddckDirPath = projectDirPath / "ddck"
        collector = _getCollector(mainWindow)

        mainWindow.editor.diagramView.deleteBlockCom(collector)

        assert not (ddckDirPath / "Collector").exists()
        trashedFilePath = ddckDirPath / ".deleted" / "Collector" / "type1.ddck"
        assert trashedFilePath.is_file()
        # The config isn't touched.
        assert (projectDirPath / "run.config").read_text() == _RUN_CONFIG

        # Sync reports the ddck as missing and ignores the trash.
        config = _rc.RunConfig.read(projectDirPath / "run.config")
        report = _sync.syncConfig(config, projectDirPath, None)
        assert [b.line for b in report.brokenIncludes] == [
            "PROJECT$ Collector/type1"
        ]
        assert not report.unusedDdckFiles

        mainWindow.undoStack.undo()

        assert (ddckDirPath / "Collector" / "type1.ddck").is_file()
        assert not (ddckDirPath / ".deleted").exists()

        mainWindow.undoStack.redo()

        assert trashedFilePath.is_file()

    def testDeletingTwiceKeepsBothFolders(self, mainWindow):
        ddckDirPath = _pl.Path(mainWindow.editor.projectFolder) / "ddck"
        (ddckDirPath / ".deleted" / "Collector").mkdir(parents=True)

        mainWindow.editor.diagramView.deleteBlockCom(_getCollector(mainWindow))

        assert (
            ddckDirPath / ".deleted" / "Collector_2" / "type1.ddck"
        ).is_file()


class TestRenameWithPrefixedIdentifiers:
    def _rename(self, mainWindow, qtbot, newName):
        editor = mainWindow.editor
        window = _cw.ComponentWindow(
            _getCollector(mainWindow),
            _pl.Path(editor.projectFolder),
            editor._createRenameHelper(),
            editor=editor,
            configFilePath=mainWindow.activeConfigFilePath,
        )
        qtbot.addWidget(window)
        window._nameLineEdit.setText(newName)
        window.accept()

    def testOnlyCheckedLinesAreRenamed(self, mainWindow, qtbot, monkeypatch):
        shown = []

        def execDialog(dialog):
            shown.append([line.identifiers for line in dialog._lines])
            return _qtw.QDialog.Accepted  # with the default check states

        monkeypatch.setattr(_pid.PrefixedIdentifiersDialog, "exec", execDialog)

        self._rename(mainWindow, qtbot, "Coll")

        assert shown == [[("CollectorArea",), ("CollectorNbModTot",)]]
        projectDirPath = _pl.Path(mainWindow.editor.projectFolder)
        assert (
            (projectDirPath / "run.config").read_text()
            == """\
string PROJECT$ "ddck"
deck CollectorArea 12
PROJECT$ generic/head
#### component: Coll ####
PROJECT$ Coll/type1
deck CollNbModTot 360
#### end component: Coll ####
PROJECT$ generic/end
"""
        )

    def testDeclining(self, mainWindow, qtbot, monkeypatch):
        monkeypatch.setattr(
            _pid.PrefixedIdentifiersDialog,
            "exec",
            lambda _: _qtw.QDialog.Rejected,
        )

        self._rename(mainWindow, qtbot, "Coll")

        projectDirPath = _pl.Path(mainWindow.editor.projectFolder)
        text = (projectDirPath / "run.config").read_text()
        assert "deck CollectorNbModTot 360" in text
        assert "PROJECT$ Coll/type1" in text
