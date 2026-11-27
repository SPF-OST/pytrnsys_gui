# pylint: disable=invalid-name  # `tmp_path` fixture
# pylint: disable=protected-access
import pathlib as _pl

import pytest as _pt
import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import trnsysGUI.componentDdcks.panel as _dlg
import trnsysGUI.runConfig as _rc

_CONFIG = """\
string PROJECT$ "ddck"
#############USED DDCKs##################
PROJECT$ generic/head
COMMON$ Solar/old as Coll
deck CollNbModTot 360

PROJECT$ generic/end
"""


@_pt.fixture(name="project")
def _project(tmp_path) -> _pl.Path:
    libraryDirPath = tmp_path / "library"
    (libraryDirPath / "Solar" / "db").mkdir(parents=True)
    (libraryDirPath / "Solar" / "db" / "TVP.ddck").write_text(
        "ASSIGN PATH$\\Solar\\db\\TVP_IAM.txt 26\n"
    )
    (libraryDirPath / "Solar" / "db" / "TVP_IAM.txt").write_text("iam")
    (libraryDirPath / "Solar" / "old.ddck").write_text("")
    (libraryDirPath / "Empty").mkdir()

    projectDirPath = tmp_path / "project"
    (projectDirPath / "ddck" / "Coll").mkdir(parents=True)
    (projectDirPath / "run.config").write_text(_CONFIG)
    return projectDirPath


def _createDialog(qtbot, projectDirPath: _pl.Path, opened=None):
    config = _rc.RunConfig.read(projectDirPath / "run.config")
    dialog = _dlg.ComponentDdckPanel(
        "Coll",
        projectDirPath,
        config,
        projectDirPath.parent / "library",
        openFile=opened.append if opened is not None else None,
    )
    qtbot.addWidget(dialog)
    return dialog


def _selectLibraryFile(dialog, relativePath: str) -> None:
    model = dialog._library.tree.model()
    matches = model.match(
        model.index(0, 0),
        _qtc.Qt.DisplayRole,
        _pl.PurePosixPath(relativePath).stem,
        hits=1,
        flags=_qtc.Qt.MatchRecursive | _qtc.Qt.MatchExactly,
    )
    assert matches, relativePath
    dialog._library.tree.setCurrentIndex(matches[0])


def _readConfig(projectDirPath: _pl.Path) -> str:
    return (projectDirPath / "run.config").read_text()


class TestComponentDdckDialog:
    def testLibraryShowsOnlyFoldersWithDdcks(self, qtbot, project):
        dialog = _createDialog(qtbot, project)

        model = dialog._library.tree.model()
        topLevelNames = [
            model.index(row, 0).data() for row in range(model.rowCount())
        ]

        assert topLevelNames == ["Solar"]

    def testAddReferenceAndApply(self, qtbot, project):
        dialog = _createDialog(qtbot, project)
        _selectLibraryFile(dialog, "Solar/db/TVP.ddck")

        dialog._addFromLibrary(asCopy=False)
        assert dialog.isModified
        assert _readConfig(project) == _CONFIG  # nothing written yet

        assert dialog.apply()

        config = _rc.RunConfig.read(project / "run.config")
        assert [i.toLine() for i in config.getComponentIncludes("Coll")] == [
            "COMMON$ Solar/db/TVP as Coll"
        ]
        assert config.getPathVariables()["COMMON$"] == str(
            _pl.Path("..") / "library"
        )

    def testCopyHappensOnlyOnApply(self, qtbot, project):
        dialog = _createDialog(qtbot, project)
        _selectLibraryFile(dialog, "Solar/db/TVP.ddck")

        dialog._addFromLibrary(asCopy=True)
        copiedFilePath = project / "ddck" / "Coll" / "TVP.ddck"
        assert not copiedFilePath.exists()

        dialog.apply()

        assert copiedFilePath.read_text() == (
            "ASSIGN PATH$\\Coll\\TVP_IAM.txt 26\n"
        )
        assert (project / "ddck" / "Coll" / "TVP_IAM.txt").is_file()
        assert "PROJECT$ Coll/TVP\n" in _readConfig(project)

    def testAsCheckboxAndName(self, qtbot, project):
        dialog = _createDialog(qtbot, project)
        _selectLibraryFile(dialog, "Solar/db/TVP.ddck")
        dialog._addFromLibrary(asCopy=False)
        asItem = dialog._table.item(0, _dlg._COLUMN_AS)
        assert asItem.checkState() == _qtc.Qt.Unchecked

        asItem.setCheckState(_qtc.Qt.Checked)
        dialog._table.item(0, _dlg._COLUMN_NAME).setText("Coll2")

        assert dialog._table.item(0, _dlg._COLUMN_AS).checkState() == (
            _qtc.Qt.Checked
        )
        assert dialog.getEntries()[0].include.toLine() == (
            "COMMON$ Solar/db/TVP as Coll2"
        )

        dialog._table.item(0, _dlg._COLUMN_AS).setCheckState(_qtc.Qt.Unchecked)
        assert dialog.getEntries()[0].include.toLine() == (
            "COMMON$ Solar/db/TVP as Coll"
        )

    def testInvalidNameIsRejected(self, qtbot, project):
        dialog = _createDialog(qtbot, project)
        _selectLibraryFile(dialog, "Solar/db/TVP.ddck")
        dialog._addFromLibrary(asCopy=False)
        dialog._table.item(0, _dlg._COLUMN_AS).setCheckState(_qtc.Qt.Checked)

        dialog._table.item(0, _dlg._COLUMN_NAME).setText("a b")

        assert dialog.getEntries()[0].include.alias == "Coll"

    def testAdoptKeepsDeckLines(self, qtbot, project):
        dialog = _createDialog(qtbot, project)
        assert not dialog._adoptionBanner.isHidden()

        dialog._adopt()
        dialog.apply()

        assert dialog._adoptionBanner.isHidden()
        # COMMON$ wasn't defined: it's added as the library.
        commonLine = f'string COMMON$ "{_pl.Path("..") / "library"}"\n'
        assert _readConfig(project) == _CONFIG.replace(
            'string PROJECT$ "ddck"\n',
            'string PROJECT$ "ddck"\n' + commonLine,
        ).replace(
            "COMMON$ Solar/old as Coll\ndeck CollNbModTot 360\n",
            "#### component: Coll ####\n"
            "COMMON$ Solar/old as Coll\n"
            "deck CollNbModTot 360\n"
            "#### end component: Coll ####\n",
        )

    def testRemoveAndReorder(self, qtbot, project):
        dialog = _createDialog(qtbot, project)
        dialog._adopt()
        _selectLibraryFile(dialog, "Solar/db/TVP.ddck")
        dialog._addFromLibrary(asCopy=False)

        dialog._table.selectRow(1)
        dialog._moveSelected(-1)
        assert [e.include.relativePath for e in dialog.getEntries()] == [
            "Solar/db/TVP",
            "Solar/old",
        ]

        dialog._table.selectRow(1)
        dialog._removeSelected()
        assert [e.include.relativePath for e in dialog.getEntries()] == [
            "Solar/db/TVP"
        ]

    def testOpenUsesResolvedPath(self, qtbot, project):
        opened: list = []
        dialog = _createDialog(qtbot, project, opened)
        dialog._adopt()

        dialog._table.cellWidget(0, _dlg._COLUMN_OPEN).click()

        assert opened == [project.parent / "library" / "Solar" / "old.ddck"]

    def testNothingIsWrittenWithoutApply(self, qtbot, project):
        dialog = _createDialog(qtbot, project)
        _selectLibraryFile(dialog, "Solar/db/TVP.ddck")
        dialog._addFromLibrary(asCopy=True)
        dialog._adopt()

        dialog.close()

        assert _readConfig(project) == _CONFIG
        assert not (project / "ddck" / "Coll" / "TVP.ddck").exists()

    def testWithoutLibrary(self, qtbot, project):
        config = _rc.RunConfig.read(project / "run.config")
        dialog = _dlg.ComponentDdckPanel("Coll", project, config, None)
        qtbot.addWidget(dialog)

        dialog._adopt()

        assert len(dialog.getEntries()) == 1


class TestAdoptionOrder:
    def testAdoptAfterAddingKeepsBlockWhereTheLinesWere(self, qtbot, project):
        dialog = _createDialog(qtbot, project)
        _selectLibraryFile(dialog, "Solar/db/TVP.ddck")
        dialog._addFromLibrary(asCopy=False)

        dialog._adopt()
        dialog.apply()

        lines = _readConfig(project).splitlines()
        blockStart = lines.index("#### component: Coll ####")
        assert lines[blockStart - 1] == "PROJECT$ generic/head"
        assert lines[blockStart + 1 : blockStart + 5] == [
            "COMMON$ Solar/old as Coll",
            "deck CollNbModTot 360",
            "COMMON$ Solar/db/TVP as Coll",
            "#### end component: Coll ####",
        ]


class TestChooseLibrary:
    def testChoosingLibraryReloadsPanelAndSavesPath(
        self, qtbot, project, monkeypatch
    ):
        config = _rc.RunConfig.read(project / "run.config")
        dialog = _dlg.ComponentDdckPanel("Coll", project, config, None)
        qtbot.addWidget(dialog)
        libraryDirPath = project.parent / "library"
        saved: list = []
        monkeypatch.setattr(_rc, "saveConfiguredLibraryPath", saved.append)
        monkeypatch.setattr(
            _qtw.QFileDialog,
            "getExistingDirectory",
            lambda *_: str(libraryDirPath),
        )

        dialog._library.chooseLibrary()

        assert saved == [str(libraryDirPath)]
        _selectLibraryFile(dialog, "Solar/db/TVP.ddck")
        dialog._addFromLibrary(asCopy=False)
        assert dialog.getEntries()[0].include.toLine() == (
            "COMMON$ Solar/db/TVP as Coll"
        )
