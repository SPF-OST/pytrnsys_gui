import os as _os
import pathlib as _pl
import shutil as _su
import subprocess as _sp
import time as _time
import typing as _tp

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import pytrnsys.utils.log as _ulog
import pytrnsys.utils.result as _res
import trnsysGUI.MassFlowVisualizer as _mfv
import trnsysGUI.TVentil as _tv
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.diagram.Editor as _de
import trnsysGUI.mainWindow as _mw
import trnsysGUI.menus.projectMenu.exportPlaceholders as _eph
import trnsysGUI.project as _prj
import trnsysGUI.storageTank.widget as _stw
import trnsysGUI.warningsAndErrors as _werrors
from . import _testHelper as _th


def getProjects() -> _tp.Iterable[_th.Project]:
    yield _th.Project.createForExampleProject("TRIHP_dualSource", exampleDirNameToCopyFrom="examplesToBeCompleted")
    yield _th.Project.createForExampleProject("icegrid")
    yield _th.Project.createForExampleProject("solar_dhw_GUI")

    yield from getTestProjects()


def getTestProjects() -> _tp.Iterable[_th.Project]:
    testProjectTestCasesDir = _th.DATA_DIR / "tests"
    testProjectTestCaseDirPaths = [tc for tc in testProjectTestCasesDir.iterdir() if tc.name != "README.txt"]
    for testProjectTestCaseDirPath in testProjectTestCaseDirPaths:
        projectName = testProjectTestCaseDirPath.name
        yield _th.Project.createForTestProject(projectName)


TEST_CASES = [_pt.param(p, id=p.testId) for p in getProjects()]


class TestEditor:
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportStorages(self, testProject: _th.Project, qtbot, monkeypatch) -> None:
        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)
        editor = mainWindow.editor

        self._exportAndTestStorageDdckFiles(editor, helper)

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportHydraulic(self, testProject: _th.Project, qtbot, monkeypatch) -> None:
        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)
        editor = mainWindow.editor

        self._exportAndTestHydraulicDdckFile(editor, helper)

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportPlaceholders(self, testProject: _th.Project, qtbot, monkeypatch) -> None:
        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)
        editor = mainWindow.editor

        self._exportAndTestDdckPlaceholdersJsonFile(editor, helper, monkeypatch)

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportDeck(self, testProject: _th.Project, qtbot, monkeypatch, shallComparisonsAlwaysSucceed=False) -> None:
        helper = _th.Helper(testProject, shallComparisonsAlwaysSucceed)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)
        editor = mainWindow.editor

        monkeypatch.chdir(helper.actualProjectFolderPath)

        self._exportAndTestStorageDdckFiles(editor, helper)

        self._exportAndTestHydraulicDdckFile(editor, helper)

        self._exportAndTestDeckFile(mainWindow, testProject, helper, monkeypatch)

    def _exportAndTestStorageDdckFiles(self, editor, helper):
        storageTankNames = self._exportStorageTanksAndGetNames(editor)
        for storageTankName in storageTankNames:
            ddckFileRelativePath = f"ddck/{storageTankName}/{storageTankName}.ddck"
            helper.ensureFilesAreEqual(ddckFileRelativePath)

    @classmethod
    def _exportStorageTanksAndGetNames(cls, editor: _de.Editor) -> _tp.Sequence[str]:  # type: ignore[name-defined]
        storageTanks = [o for o in editor.trnsysObj if isinstance(o, _stw.StorageTank)]  # pylint: disable=no-member

        for storageTank in storageTanks:
            storageTank.exportDck()

        storageTankNames = [t.displayName for t in storageTanks]

        return storageTankNames

    @staticmethod
    def _exportAndTestHydraulicDdckFile(editor, helper):
        editor.exportHydraulics(exportTo="ddck")
        hydraulicDdckRelativePath = "ddck/hydraulic/hydraulic.ddck"
        helper.ensureFilesAreEqual(hydraulicDdckRelativePath)

    @staticmethod
    def _exportAndTestDdckPlaceholdersJsonFile(editor, helper, monkeypatch):
        def dummyInformation(*_, **__):
            return _qtw.QMessageBox.Ok

        monkeypatch.setattr(
            _qtw.QMessageBox, _qtw.QMessageBox.information.__name__, dummyInformation  # pylint: disable=no-member
        )

        result = _eph.exportDdckPlaceHolderValuesJsonFile(editor)

        assert not _res.isError(result), _res.error(result).message

        helper.ensureFilesAreEqual("DdckPlaceHolderValues.json")

    def _exportAndTestDeckFile(self, mainWindow, testProject, helper, monkeypatch):
        def dummyInformation(*_, **__):
            return _qtw.QMessageBox.Ok

        monkeypatch.setattr(
            _qtw.QMessageBox, _qtw.QMessageBox.information.__name__, dummyInformation  # pylint: disable=no-member
        )

        def dummyShowErrorMessageBox(errorMessage: str, title: str = "Error") -> None:
            failMessage = f"{title}: {errorMessage}"
            _pt.fail(failMessage)

        monkeypatch.setattr(_werrors, _werrors.showMessageBox.__name__, dummyShowErrorMessageBox)

        mainWindow.exportDck()

        deckFileName = f"{testProject.projectName}.dck"

        pathPrefixes = self._getHardCodedPathPrefixesForReplacingInExpectedDeck()
        helper.ensureFilesAreEqual(deckFileName, replaceInExpected=pathPrefixes)

    @staticmethod
    def _getHardCodedPathPrefixesForReplacingInExpectedDeck():
        hardCodedPathPrefixInExpectedDeck = r"C:\actions-runner\_work\pytrnsys_gui\pytrnsys_gui\tests\trnsysGUI\diagram"

        hardCodedPathPrefixInActualDeck = str(_pl.Path(__file__).parent)

        pathPrefixes = (hardCodedPathPrefixInExpectedDeck, hardCodedPathPrefixInActualDeck)

        return pathPrefixes

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testSaveAndReloadProject(
        self, testProject: _th.Project, qtbot, monkeypatch
    ) -> None:  # pylint: disable=too-many-locals
        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)

        convertedProjectFolderPath = helper.actualProjectFolderPath.parent / "converted"
        if convertedProjectFolderPath.exists():
            _su.rmtree(convertedProjectFolderPath)
            _time.sleep(1)
        _os.mkdir(convertedProjectFolderPath)

        mainWindow.copyContentsToNewFolder(convertedProjectFolderPath, helper.actualProjectFolderPath)

        convertedJsonFilePath = convertedProjectFolderPath / f"{convertedProjectFolderPath.name}.json"
        convertedProject = _prj.LoadProject(convertedJsonFilePath)
        _mw.MainWindow(logger, convertedProject)  # type: ignore[attr-defined]

    @_pt.mark.needs_trnsys
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testMassFlowSolver(
        self, testProject: _th.Project, qtbot, monkeypatch, shallComparisonsAlwaysSucceed=False
    ) -> None:
        helper = _th.Helper(testProject, shallComparisonsAlwaysSucceed)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)

        self._exportMassFlowSolverDeckAndRunTrnsys(mainWindow.editor)

        massFlowSolverDeckFileName = f"{testProject.projectName}_mfs.dck"
        helper.ensureFilesAreEqual(massFlowSolverDeckFileName)

        massFlowRatesPrintFileName = f"{testProject.projectName}_Mfr.prt"
        helper.ensureDataFramesAreEqual(massFlowRatesPrintFileName)

        temperaturesPintFileName = f"{testProject.projectName}_T.prt"
        helper.ensureDataFramesAreEqual(temperaturesPintFileName)

        massFlowRatesPrintFilePath = helper.actualProjectFolderPath / massFlowRatesPrintFileName
        temperaturesPrintFilePath = helper.actualProjectFolderPath / temperaturesPintFileName
        self._assertMassFlowVisualizerLoadsData(massFlowRatesPrintFilePath, temperaturesPrintFilePath, mainWindow)

    @classmethod
    def _createMainWindow(cls, helper, qtbot, monkeypatch):
        cls._configureDontAskWhetherWindowShouldBeClosed(monkeypatch)

        projectFolderPath = helper.actualProjectFolderPath
        projectJsonFilePath = projectFolderPath / f"{projectFolderPath.name}.json"
        project = _prj.LoadProject(projectJsonFilePath)

        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

        mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

        qtbot.addWidget(mainWindow)

        return mainWindow

    @staticmethod
    def _configureDontAskWhetherWindowShouldBeClosed(monkeypatch) -> None:
        def patchedCloseEvent(_, closeEvent):
            return closeEvent.accept()

        monkeypatch.setattr(
            _mw.MainWindow,  # type: ignore[attr-defined]
            _mw.MainWindow.closeEvent.__name__,  # type: ignore[attr-defined]
            patchedCloseEvent,
        )

    @staticmethod
    def _assertMassFlowVisualizerLoadsData(
        massFlowRatesPrintFilePath: _pl.Path,
        temperaturesPrintFilePath: _pl.Path,
        mainWindow: _mw.MainWindow,  # type: ignore[name-defined]
    ):
        blockItemsAndConnections = mainWindow.editor.trnsysObj
        singlePipeConnections = [o for o in blockItemsAndConnections if isinstance(o, _spc.SinglePipeConnection)]
        valves = [o for o in blockItemsAndConnections if isinstance(o, _tv.TVentil)]

        for singlePipeConnection in singlePipeConnections:
            singlePipeConnection.massFlowLabel.setPlainText("")

        for valve in valves:
            valve.posLabel.setPlainText("")

        massFlowSolverVisualizer = _mfv.MassFlowVisualizer(  # type: ignore[attr-defined]  # pylint: disable=unused-variable
            mainWindow, massFlowRatesPrintFilePath, temperaturesPrintFilePath
        )

        areAllMassFlowLabelsSet = all(c.massFlowLabel.toPlainText() for c in singlePipeConnections)
        areAllValvePositionLabelsSet = all(v.posLabel.toPlainText() for v in valves)
        assert areAllMassFlowLabelsSet and areAllValvePositionLabelsSet

    def _exportMassFlowSolverDeckAndRunTrnsys(self, editor: _de.Editor):  # type: ignore[name-defined]
        exportedFilePath = self._exportHydraulic(editor, _format="mfs")

        trnExePath = self._getTrnExePath()

        _sp.run([str(trnExePath), str(exportedFilePath), "/H"], check=True)

    @staticmethod
    def _getTrnExePath():
        isRunDuringCi = _os.environ.get("CI") == "true"
        if isRunDuringCi:
            return _pl.PureWindowsPath(r"C:\CI-Progams\TRNSYS18\Exe\TrnEXE.exe")

        return _pl.PureWindowsPath(r"C:\TRNSYS18\Exe\TrnEXE.exe")

    @classmethod
    def _exportHydraulic(cls, editor: _de.Editor, *, _format) -> str:  # type: ignore[name-defined]
        exportedFilePath = editor.exportHydraulics(exportTo=_format)
        return exportedFilePath

    @_pt.mark.tool
    @_pt.mark.skip("This test is really a script to be run by the user from the IDE to update the expected files.")
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testToolUpdateExportDeckExpectedFiles(self, testProject: _th.Project, qtbot, monkeypatch) -> None:
        shallComparisonsAlwaysSucceed = True
        self.testExportDeck(testProject, qtbot, monkeypatch, shallComparisonsAlwaysSucceed)

        self._updateExpectedFiles(testProject)

    @_pt.mark.tool
    @_pt.mark.skip("This test is really a script to be run by the user from the IDE to update the expected files.")
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testToolUpdateMassFlowSolverExpectedFiles(self, testProject: _th.Project, qtbot, monkeypatch) -> None:
        shallComparisonsAlwaysSucceed = True
        self.testMassFlowSolver(testProject, qtbot, monkeypatch, shallComparisonsAlwaysSucceed)

        self._updateExpectedFiles(testProject)

    def _updateExpectedFiles(self, testProject):
        helper = _th.Helper(testProject)
        _su.copytree(helper.actualProjectFolderPath, helper.expectedProjectFolderPath, dirs_exist_ok=True)
        self._resetHardCodedPathsInDeckFile(testProject, helper)

    def _resetHardCodedPathsInDeckFile(self, project: _th.Project, helper: _th.Helper) -> None:
        deckFilePath = helper.expectedProjectFolderPath / f"{project.projectName}.dck"
        (
            hardcodedPathInExpectedDeck,
            hardCodedPathInActualDeck,
        ) = self._getHardCodedPathPrefixesForReplacingInExpectedDeck()
        deckFileContent = deckFilePath.read_text(encoding="windows-1252")
        updatedDeckFileContent = deckFileContent.replace(hardCodedPathInActualDeck, hardcodedPathInExpectedDeck)
        deckFilePath.write_text(updatedDeckFileContent, encoding="windows-1252")
