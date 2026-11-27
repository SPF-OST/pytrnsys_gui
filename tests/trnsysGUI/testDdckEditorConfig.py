# pylint: disable=invalid-name  # `tmp_path` fixture
# pylint: disable=protected-access
import pathlib as _pl

import pytest as _pt
import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import pytrnsys.ddck.replaceTokens.defaultVisibility as _dv
import trnsysGUI.ddckEditor.tab as _tab
import trnsysGUI.runConfig as _rc
import trnsysGUI.runConfig.context as _ctx

_CONFIG = """\
string PROJECT$ "ddck"
string COMMON$ "../library"
string defaultVisibility "global"
#############USED DDCKs##################
COMMON$ generic/head global
#### component: Coll ####
COMMON$ Solar/collector as Coll
#### end component: Coll ####
#### component: Coll2 ####
COMMON$ Solar/collector as Coll2
#### end component: Coll2 ####
PROJECT$ control/control
PROJECT$ missing/file
"""

_COLLECTOR_DDCK = """\
*******************************
** collector
*******************************
EQUATIONS 1
TIn = @temp(In)
"""


@_pt.fixture(name="context")
def _context(tmp_path) -> _ctx.ConfigContext:
    libraryDirPath = tmp_path / "library"
    (libraryDirPath / "Solar").mkdir(parents=True)
    (libraryDirPath / "generic").mkdir()
    (libraryDirPath / "Solar" / "collector.ddck").write_text(_COLLECTOR_DDCK)
    (libraryDirPath / "generic" / "head.ddck").write_text(
        "*\n** head\n*\nCONSTANTS 1\nx = 1\n"
    )

    projectDirPath = tmp_path / "project"
    (projectDirPath / "ddck" / "control").mkdir(parents=True)
    (projectDirPath / "ddck" / "control" / "control.ddck").write_text(
        "*\n** control\n*\nCONSTANTS 1\nc = 1\n"
    )
    configFilePath = projectDirPath / "run.config"
    configFilePath.write_text(_CONFIG)

    return _ctx.ConfigContext(
        _rc.RunConfig.read(configFilePath), projectDirPath, libraryDirPath
    )


@_pt.fixture(name="editorTab")
def _editorTab(qtbot, context) -> _tab.DdckEditorTab:
    def getContext():
        configFilePath = context.config.filePath
        return _ctx.ConfigContext(
            _rc.RunConfig.read(configFilePath),
            context.projectDirPath,
            context.libraryDirPath,
        )

    editorTab = _tab.DdckEditorTab(
        lambda: {
            "Coll": {"In": {"@temp": "TCollIn"}},
            "Coll2": {"In": {"@temp": "TColl2In"}},
        },
        configContextProvider=getContext,
    )
    qtbot.addWidget(editorTab)
    editorTab.refreshConfigContext()
    return editorTab


class TestContext:
    def testFindInclusions(self, context):
        collector = context.libraryDirPath / "Solar" / "collector.ddck"
        head = context.libraryDirPath / "generic" / "head.ddck"
        control = context.projectDirPath / "ddck" / "control" / "control.ddck"

        collectorInclusions = _ctx.findInclusions(context, collector)
        headInclusions = _ctx.findInclusions(context, head)

        assert [i.componentName for i in collectorInclusions] == [
            "Coll",
            "Coll2",
        ]
        assert [i.blockComponentName for i in collectorInclusions] == [
            "Coll",
            "Coll2",
        ]
        # `defaultVisibility "global"` in the config:
        assert collectorInclusions[0].defaultVisibility == (
            _dv.DefaultVisibility.GLOBAL
        )
        assert headInclusions[0].include.isGlobal
        assert _ctx.findInclusions(context, control)[0].componentName == (
            "control"
        )
        assert context.isLibraryFile(collector)
        assert not context.isLibraryFile(control)

    def testDefaultVisibilityDefaultsToLocal(self):
        assert _ctx.getDefaultVisibility(_rc.RunConfig("")) == (
            _dv.DefaultVisibility.LOCAL
        )


class TestEditorWithConfig:
    def testConfigTree(self, editorTab, context):
        tree = editorTab._configTree.tree
        topLevelTexts = [
            tree.topLevelItem(i).text(0)
            for i in range(tree.topLevelItemCount())
        ]

        assert topLevelTexts == [
            "generic/head  (global)",
            "Coll",
            "Coll2",
            "control/control",
            "missing/file",
        ]
        missing = tree.topLevelItem(4)
        assert missing.data(0, _qtc.Qt.UserRole) is None

        editorTab._configTree._onItemActivated(tree.topLevelItem(3))
        document = editorTab._getCurrentDocument()
        assert (
            document.filePath
            == (
                context.projectDirPath / "ddck" / "control" / "control.ddck"
            ).resolve()
        )
        assert not document.isLocked

    def testValidateAsChoosesComponent(self, editorTab, context):
        editorTab.openFile(context.libraryDirPath / "Solar" / "collector.ddck")
        document = editorTab._getCurrentDocument()

        assert document.inclusionComboBox.count() == 2
        assert document.componentName == "Coll"
        assert document.valuesByPort == {"In": {"@temp": "TCollIn"}}
        assert not document.problems

        document.inclusionComboBox.setCurrentIndex(1)

        assert document.componentName == "Coll2"
        assert document.valuesByPort == {"In": {"@temp": "TColl2In"}}

    def testLibraryOriginalIsLockedUntilUnlocked(
        self, editorTab, context, monkeypatch
    ):
        filePath = context.libraryDirPath / "generic" / "head.ddck"
        editorTab.openFile(filePath)
        document = editorTab._getCurrentDocument()
        warnings = []
        monkeypatch.setattr(
            _tab, "_showWarning", lambda *a: warnings.append(a)
        )

        assert document.isLocked
        assert document.lockBanner.isVisibleTo(document)
        assert not editorTab.saveDocument(document)
        assert warnings

        monkeypatch.setattr(
            _qtw.QMessageBox, "question", lambda *_: _qtw.QMessageBox.Yes
        )
        document.lockBanner.unlockRequested.emit()
        editorTab.refreshConfigContext()  # stays unlocked

        assert not document.isLocked
        document.editor.appendPlainText("y = 2")
        assert editorTab.saveDocument(document)
        assert filePath.read_text().endswith("y = 2")

    def testCopyComponentDdckToProject(self, editorTab, context):
        libraryFilePath = context.libraryDirPath / "Solar" / "collector.ddck"
        editorTab.openFile(libraryFilePath)
        document = editorTab._getCurrentDocument()
        document.inclusionComboBox.setCurrentIndex(1)  # Coll2

        document.lockBanner.copyRequested.emit()

        copiedFilePath = (
            context.projectDirPath / "ddck" / "Coll2" / ("collector.ddck")
        )
        assert copiedFilePath.read_text() == _COLLECTOR_DDCK
        config = _rc.RunConfig.read(context.config.filePath)
        assert [i.toLine() for i in config.getComponentIncludes("Coll2")] == [
            "PROJECT$ Coll2/collector"
        ]
        # Coll still uses the library's original.
        assert [i.toLine() for i in config.getComponentIncludes("Coll")] == [
            "COMMON$ Solar/collector as Coll"
        ]
        newDocument = editorTab._getCurrentDocument()
        assert newDocument.filePath == copiedFilePath.resolve()
        assert not newDocument.isLocked
        assert newDocument.componentName == "Coll2"

    def testWithoutConfig(self, qtbot, context):
        editorTab = _tab.DdckEditorTab(lambda: None)
        qtbot.addWidget(editorTab)
        editorTab.refreshConfigContext()

        editorTab.openFile(context.libraryDirPath / "Solar" / "collector.ddck")

        document = editorTab._getCurrentDocument()
        assert not document.isLocked
        assert document.componentName == "Solar"
