# pylint: disable=invalid-name  # `tmp_path` fixture
# pylint: disable=protected-access
import pathlib as _pl

import pytest as _pt
import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import trnsysGUI.componentDdcks.projectWindow as _pw
import trnsysGUI.runConfig as _rc

_CONFIG = """\
string PROJECT$ "ddck"
#############USED DDCKs##################
PROJECT$ generic/head
#### component: Coll ####
COMMON$ Solar/type1 as Coll
deck CollA 2
#### end component: Coll ####
PROJECT$ control/control
deck CtrlOn 1
PROJECT$ generic/end
"""


@_pt.fixture(name="project")
def _project(tmp_path) -> _pl.Path:
    libraryDirPath = tmp_path / "library"
    (libraryDirPath / "Weather_SPF" / "Meteo").mkdir(parents=True)
    (libraryDirPath / "Weather_SPF" / "Meteo" / "city.ddck").write_text(
        "ASSIGN PATH$\\Weather_SPF\\Meteo\\city.dat 30\n"
    )
    (libraryDirPath / "Weather_SPF" / "Meteo" / "city.dat").write_text("data")
    (libraryDirPath / "generic").mkdir()
    (libraryDirPath / "generic" / "printer.ddck").write_text("")

    projectDirPath = tmp_path / "project"
    for folder in ["generic", "control", "weather", "Coll"]:
        (projectDirPath / "ddck" / folder).mkdir(parents=True)
    (projectDirPath / "ddck" / "control" / "control.ddck").write_text("")
    (projectDirPath / "run.config").write_text(_CONFIG)
    return projectDirPath


def _createWindow(qtbot, projectDirPath, opened=None) -> _pw.ProjectDdckWindow:
    config = _rc.RunConfig.read(projectDirPath / "run.config")
    window = _pw.ProjectDdckWindow(
        projectDirPath,
        config,
        projectDirPath.parent / "library",
        componentNames=["Coll"],
        openFile=opened.append if opened is not None else None,
    )
    qtbot.addWidget(window)
    return window


def _rowTexts(window) -> list[str]:
    table = window._table
    return [
        table.item(row, _pw._COLUMN_DDCK).text()
        for row in range(table.rowCount())
    ]


def _readConfig(projectDirPath: _pl.Path) -> str:
    return (projectDirPath / "run.config").read_text()


class TestProjectDdckWindow:
    def testRowsInConfigOrderWithBlocks(self, qtbot, project):
        window = _createWindow(qtbot, project)

        assert _rowTexts(window) == [
            "generic/head",
            "▸ Coll   (1 ddck)",
            "control/control   (+1 lines)",
            "generic/end",
        ]
        assert window._orderWarningLabel.isHidden()

    def testMoveBlockAndWarnAboutEnd(self, qtbot, project):
        window = _createWindow(qtbot, project)

        window._table.selectRow(1)
        window._moveSelected(1)
        window._moveSelected(1)

        assert _rowTexts(window)[-1] == "▸ Coll   (1 ddck)"
        assert "`end` should be the last" in window._orderWarningLabel.text()
        assert _readConfig(project) == _CONFIG  # not before OK

        window.apply()
        assert _readConfig(project).endswith(
            "PROJECT$ generic/end\n"
            "#### component: Coll ####\n"
            "COMMON$ Solar/type1 as Coll\n"
            "deck CollA 2\n"
            "#### end component: Coll ####\n"
        )

    def testGlobalAndAsAreExclusive(self, qtbot, project):
        window = _createWindow(qtbot, project)

        window._table.item(2, _pw._COLUMN_GLOBAL).setCheckState(
            _qtc.Qt.Checked
        )
        assert window.config.getSectionItems()[2].entry.include.toLine() == (
            "PROJECT$ control/control global"
        )

        window._table.item(2, _pw._COLUMN_AS).setCheckState(_qtc.Qt.Checked)
        window._table.item(2, _pw._COLUMN_NAME).setText("Ctrl")

        assert window.config.getSectionItems()[2].entry.include.toLine() == (
            "PROJECT$ control/control as Ctrl"
        )
        assert window.config.getSectionItems()[2].entry.trailingLines == (
            "deck CtrlOn 1",
        )

    def testUseOriginalAddsReferenceBeforeEnd(self, qtbot, project):
        window = _createWindow(qtbot, project)
        libraryDirPath = project.parent / "library"

        window._useOriginal(libraryDirPath / "generic" / "printer.ddck")
        window.apply()

        config = _rc.RunConfig.read(project / "run.config")
        lines = [il.include.toLine() for il in config.getIncludeLines()]
        assert lines[-2:] == [
            "COMMON$ generic/printer",
            "PROJECT$ generic/end",
        ]
        assert "COMMON$" in config.getPathVariables()

    def testImportAsCopyIntoChosenFolder(self, qtbot, project, monkeypatch):
        window = _createWindow(qtbot, project)
        offered = []

        def getItem(*args):
            offered.append(args[3])
            return args[3][0], True

        monkeypatch.setattr(_qtw.QInputDialog, "getItem", getItem)
        libraryDirPath = project.parent / "library"

        window._importAsCopy(
            libraryDirPath / "Weather_SPF" / "Meteo" / "city.ddck"
        )

        # `weather` exists and matches `Weather_SPF`; component folders are
        # not offered.
        assert offered == [["weather", "control", "generic"]]
        copiedFilePath = project / "ddck" / "weather" / "city.ddck"
        assert not copiedFilePath.exists()

        window.apply()

        # The data file next to the ddck is copied with it.
        assert copiedFilePath.read_text() == (
            "ASSIGN PATH$\\weather\\city.dat 30\n"
        )
        assert (project / "ddck" / "weather" / "city.dat").is_file()
        assert "PROJECT$ weather/city\n" in _readConfig(project)

    def testRemoveBlockAsksFirst(self, qtbot, project, monkeypatch):
        window = _createWindow(qtbot, project)
        monkeypatch.setattr(
            _qtw.QMessageBox, "question", lambda *_: _qtw.QMessageBox.No
        )
        window._table.selectRow(1)

        window._removeSelected()
        assert len(_rowTexts(window)) == 4

        monkeypatch.setattr(
            _qtw.QMessageBox, "question", lambda *_: _qtw.QMessageBox.Yes
        )
        window._removeSelected()
        assert "▸ Coll   (1 ddck)" not in _rowTexts(window)

    def testOpenResolvesProjectDdck(self, qtbot, project):
        opened: list = []
        window = _createWindow(qtbot, project, opened)

        window._table.cellWidget(2, _pw._COLUMN_OPEN).click()

        assert opened == [project / "ddck" / "control" / "control.ddck"]


class TestFolderSuggestions:
    def testFallsBackToLibraryFolder(self, tmp_path):
        (tmp_path / "control").mkdir()

        suggestions = _pw.getFolderSuggestions(
            tmp_path, [], _pl.PurePath("Loads/DHW/Database/mfh.ddck")
        )

        assert suggestions == ["Database", "control"]
