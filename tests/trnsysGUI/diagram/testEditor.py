import json as _json
import os as _os
import pathlib as _pl
import re as _re
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
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler
from . import _testHelper as _th


def getProjects() -> _tp.Iterable[_th.Project]:
    yield _th.Project.createForExampleProject(
        "TRIHP_dualSource", exampleDirNameToCopyFrom="examplesToBeCompleted"
    )
    yield _th.Project.createForExampleProject("icegrid")

    resultsDirPath = _pl.Path("results")
    loadDiagramWarning = _th.LoadDiagramWarning(
        "Orphaned ddck folders",
        "The following ddck folder does not have a corresponding component in the diagram:\n\tdhw_demand",
    )
    yield _th.Project.createForExampleProject(
        "solar_dhw_GUI",
        resultsDirPath=resultsDirPath,
        loadDiagramWarning=loadDiagramWarning,
    )

    yield from getTestProjects()


def getTestProjects() -> _tp.Iterable[_th.Project]:
    testProjectTestCasesDir = _th.DATA_DIR / "tests"
    testProjectTestCaseDirPaths = [
        tc
        for tc in testProjectTestCasesDir.iterdir()
        if tc.name != "README.txt"
    ]
    for testProjectTestCaseDirPath in testProjectTestCaseDirPaths:
        projectName = testProjectTestCaseDirPath.name
        yield _th.Project.createForTestProject(projectName)


TEST_CASES = [_pt.param(p, id=p.testId) for p in getProjects()]


class TestEditor:
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportStorages(
        self, testProject: _th.Project, qtbot, monkeypatch
    ) -> None:
        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow, _ = self._createMainWindowAndWarningHelper(
            helper, testProject.loadDiagramWarningOrNone, qtbot, monkeypatch
        )

        editor = mainWindow.editor

        self._exportAndTestStorageDdckFiles(editor, helper)

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportHydraulic(
        self, testProject: _th.Project, qtbot, monkeypatch
    ) -> None:
        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow, _ = self._createMainWindowAndWarningHelper(
            helper, testProject.loadDiagramWarningOrNone, qtbot, monkeypatch
        )

        editor = mainWindow.editor

        self._exportAndTestHydraulicDdckFile(editor, helper)

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportPlaceholders(
        self, testProject: _th.Project, qtbot, monkeypatch
    ) -> None:
        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow, _ = self._createMainWindowAndWarningHelper(
            helper, testProject.loadDiagramWarningOrNone, qtbot, monkeypatch
        )

        editor = mainWindow.editor

        self._exportAndTestDdckPlaceholdersJsonFile(
            editor, helper, monkeypatch
        )

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportDeck(
        self,
        testProject: _th.Project,
        qtbot,
        monkeypatch,
        shallComparisonsAlwaysSucceed=False,
    ) -> None:
        helper = _th.Helper(testProject, shallComparisonsAlwaysSucceed)
        helper.setup()

        mainWindow, _ = self._createMainWindowAndWarningHelper(
            helper, testProject.loadDiagramWarningOrNone, qtbot, monkeypatch
        )
        editor = mainWindow.editor

        monkeypatch.chdir(helper.actualProjectFolderPath)

        self._exportAndTestStorageDdckFiles(editor, helper)

        self._exportAndTestHydraulicDdckFile(editor, helper)

        self._exportAndTestDeckFile(
            mainWindow, testProject, helper, monkeypatch
        )

    def _exportAndTestStorageDdckFiles(self, editor, helper):
        storageTankNames = self._exportStorageTanksAndGetNames(editor)
        for storageTankName in storageTankNames:
            ddckFileRelativePath = (
                f"ddck/{storageTankName}/{storageTankName}.ddck"
            )
            helper.ensureFilesAreEqual(ddckFileRelativePath)

    @classmethod
    def _exportStorageTanksAndGetNames(cls, editor: _de.Editor) -> _tp.Sequence[str]:  # type: ignore[name-defined]
        storageTanks = [
            o for o in editor.trnsysObj if isinstance(o, _stw.StorageTank)
        ]  # pylint: disable=no-member

        for storageTank in storageTanks:
            storageTank.exportDck()

        storageTankNames = [t.displayName for t in storageTanks]

        return storageTankNames

    @staticmethod
    def _exportAndTestHydraulicDdckFile(editor, helper):
        editor.exportHydraulics(
            exportTo="ddck", massFlowSolver=editor.massFlowSolver
        )
        hydraulicDdckRelativePath = "ddck/hydraulic/hydraulic.ddck"
        helper.ensureFilesAreEqual(hydraulicDdckRelativePath)

    @staticmethod
    def _exportAndTestDdckPlaceholdersJsonFile(editor, helper, monkeypatch):
        def dummyInformation(*_, **__):
            return _qtw.QMessageBox.Ok

        monkeypatch.setattr(
            _qtw.QMessageBox,
            _qtw.QMessageBox.information.__name__,  # pylint: disable=no-member
            dummyInformation,
        )

        result = _eph.exportDdckPlaceHolderValuesJsonFile(editor)

        assert not _res.isError(result), _res.error(result).message

        helper.ensureFilesAreEqual("DdckPlaceHolderValues.json")

    def _exportAndTestDeckFile(
        self, mainWindow, testProject, helper, monkeypatch
    ):
        def dummyInformation(*_, **__):
            return _qtw.QMessageBox.Ok

        monkeypatch.setattr(
            _qtw.QMessageBox,
            _qtw.QMessageBox.information.__name__,  # pylint: disable=no-member
            dummyInformation,
        )

        def dummyShowErrorMessageBox(
            errorMessage: str, title: str = "Error"
        ) -> None:
            failMessage = f"{title}: {errorMessage}"
            _pt.fail(failMessage)

        monkeypatch.setattr(
            _werrors,
            _werrors.showMessageBox.__name__,
            dummyShowErrorMessageBox,
        )

        mainWindow.exportDck()

        deckFileName = f"{testProject.projectName}.dck"
        relativeDeckFilePathAsString = (
            testProject.resultsDirPathOrNone / deckFileName
            if testProject.resultsDirPathOrNone
            else deckFileName
        )

        pathPrefixes = (
            self._getHardCodedPathPrefixesForReplacingInExpectedDeck()
        )

        helper.ensureFilesAreEqual(
            relativeDeckFilePathAsString, replaceInExpected=pathPrefixes
        )

    @staticmethod
    def _getHardCodedPathPrefixesForReplacingInExpectedDeck():
        hardCodedPathPrefixInExpectedDeck = r"C:\actions-runner\_work\pytrnsys_gui\pytrnsys_gui\tests\trnsysGUI\diagram"

        hardCodedPathPrefixInActualDeck = str(_pl.Path(__file__).parent)

        pathPrefixes = (
            hardCodedPathPrefixInExpectedDeck,
            hardCodedPathPrefixInActualDeck,
        )

        return pathPrefixes

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testSaveAndReloadProject(
        self, testProject: _th.Project, qtbot, monkeypatch
    ) -> None:  # pylint: disable=too-many-locals
        monkeypatch.setattr(
            RecentProjectsHandler,
            RecentProjectsHandler.addProject.__name__,
            lambda path: None,
        )
        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow, warningHelper = self._createMainWindowAndWarningHelper(
            helper, testProject.loadDiagramWarningOrNone, qtbot, monkeypatch
        )

        convertedProjectFolderPath = (
            helper.actualProjectFolderPath.parent / "converted"
        )
        if convertedProjectFolderPath.exists():
            _su.rmtree(convertedProjectFolderPath)
            _time.sleep(1)
        _os.mkdir(convertedProjectFolderPath)

        warningHelper.reset()
        mainWindow.copyContentsToNewFolder(
            convertedProjectFolderPath, helper.actualProjectFolderPath
        )
        warningHelper.verifyOrRaise()

        convertedJsonFilePath = (
            convertedProjectFolderPath
            / f"{convertedProjectFolderPath.name}.json"
        )
        convertedProject = _prj.LoadProject(convertedJsonFilePath)

        warningHelper.reset()
        _mw.MainWindow(logger, convertedProject)  # type: ignore[attr-defined]
        warningHelper.verifyOrRaise()

    @_pt.mark.needs_trnsys
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testMassFlowSolver(
        self,
        testProject: _th.Project,
        qtbot,
        monkeypatch,
        shallComparisonsAlwaysSucceed=False,
    ) -> None:
        helper = _th.Helper(testProject, shallComparisonsAlwaysSucceed)
        helper.setup()

        mainWindow, _ = self._createMainWindowAndWarningHelper(
            helper, testProject.loadDiagramWarningOrNone, qtbot, monkeypatch
        )

        self._exportMassFlowSolverDeckAndRunTrnsys(mainWindow.editor)

        massFlowSolverDeckFileName = f"{testProject.projectName}_mfs.dck"
        helper.ensureFilesAreEqual(massFlowSolverDeckFileName)

        massFlowRatesPrintFileName = f"{testProject.projectName}_Mfr.prt"
        helper.ensureDataFramesAreEqual(massFlowRatesPrintFileName)

        temperaturesPintFileName = f"{testProject.projectName}_T.prt"
        helper.ensureDataFramesAreEqual(temperaturesPintFileName)

        massFlowRatesPrintFilePath = (
            helper.actualProjectFolderPath / massFlowRatesPrintFileName
        )
        temperaturesPrintFilePath = (
            helper.actualProjectFolderPath / temperaturesPintFileName
        )
        self._assertMassFlowVisualizerLoadsData(
            massFlowRatesPrintFilePath, temperaturesPrintFilePath, mainWindow
        )

    @staticmethod
    def _getTestProjectByName(projectName: str) -> _th.Project:
        return next(
            p for p in getTestProjects() if p.projectName == projectName
        )

    @staticmethod
    def _copyTestProjectToTmpPath(
        testProject: _th.Project,
        tmp_path: _pl.Path,  # pylint: disable=invalid-name
    ) -> _pl.Path:
        sourceProjectFolderPath = (
            _th.DATA_DIR
            / "tests"
            / testProject.projectName
            / testProject.projectName
        )
        targetProjectFolderPath = tmp_path / testProject.projectName
        _su.copytree(sourceProjectFolderPath, targetProjectFolderPath)
        return targetProjectFolderPath

    @staticmethod
    def _getProjectJsonFilePath(projectFolderPath: _pl.Path) -> _pl.Path:
        return projectFolderPath / f"{projectFolderPath.name}.json"

    def _createMainWindowInTmpPath(
        self,
        qtbot,
        monkeypatch,
        tmp_path: _pl.Path,  # pylint: disable=invalid-name
    ) -> _mw.MainWindow:  # type: ignore[name-defined]
        monkeypatch.setattr(
            RecentProjectsHandler,
            RecentProjectsHandler.addProject.__name__,
            lambda path: None,
        )
        self._configureDontAskWhetherWindowShouldBeClosed(monkeypatch)
        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]
        projectFolderPath = self._copyTestProjectToTmpPath(
            self._getTestProjectByName("storage-tank"), tmp_path
        )
        projectJsonFilePath = self._getProjectJsonFilePath(projectFolderPath)
        mainWindow = _mw.MainWindow(  # type: ignore[attr-defined]
            logger, _prj.LoadProject(projectJsonFilePath)
        )
        qtbot.addWidget(mainWindow)
        return mainWindow

    @staticmethod
    def _removeMassFlowSolverKeyFromProjectJson(
        projectJsonFilePath: _pl.Path,
    ) -> None:
        projectJson = _json.loads(
            projectJsonFilePath.read_text(encoding="utf-8")
        )
        del projectJson["massFlowSolver"]
        projectJsonFilePath.write_text(
            _json.dumps(projectJson, indent=4, sort_keys=True),
            encoding="utf-8",
        )

    def testProjectWithoutMassFlowSolverKeyLoadsAsType9352(
        self, qtbot, monkeypatch, tmp_path  # pylint: disable=invalid-name
    ) -> None:
        mainWindow = self._createMainWindowInTmpPath(
            qtbot, monkeypatch, tmp_path
        )
        projectJsonFilePath = self._getProjectJsonFilePath(
            _pl.Path(mainWindow.projectFolder)
        )
        self._removeMassFlowSolverKeyFromProjectJson(projectJsonFilePath)

        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]
        mainWindow = _mw.MainWindow(  # type: ignore[attr-defined]
            logger, _prj.LoadProject(projectJsonFilePath)
        )
        qtbot.addWidget(mainWindow)

        assert mainWindow.editor.massFlowSolver == "type9352"

    def testNewProjectUsesJuliaSolverAndKeepsItWhenSaved(
        self, qtbot, monkeypatch, tmp_path  # pylint: disable=invalid-name
    ) -> None:
        monkeypatch.setattr(
            RecentProjectsHandler,
            RecentProjectsHandler.addProject.__name__,
            lambda path: None,
        )
        self._configureDontAskWhetherWindowShouldBeClosed(monkeypatch)
        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

        newProjectFolderPath = tmp_path / "new-project" / "new-project"
        newProjectFolderPath.mkdir(parents=True)
        newProjectJsonFilePath = self._getProjectJsonFilePath(
            newProjectFolderPath
        )

        mainWindow = _mw.MainWindow(  # type: ignore[attr-defined]
            logger, _prj.CreateProject(newProjectJsonFilePath)
        )
        qtbot.addWidget(mainWindow)
        assert mainWindow.editor.massFlowSolver == "julia"

        mainWindow.editor.saveProject(showWarning=False)
        savedProjectJson = _json.loads(
            newProjectJsonFilePath.read_text(encoding="utf-8")
        )
        assert savedProjectJson["massFlowSolver"] == "julia"

        mainWindow = _mw.MainWindow(  # type: ignore[attr-defined]
            logger, _prj.LoadProject(newProjectJsonFilePath)
        )
        qtbot.addWidget(mainWindow)
        assert mainWindow.editor.massFlowSolver == "julia"

    def testSaveAndReloadKeepsChangedMassFlowSolverSetting(
        self, qtbot, monkeypatch, tmp_path  # pylint: disable=invalid-name
    ) -> None:
        mainWindow = self._createMainWindowInTmpPath(
            qtbot, monkeypatch, tmp_path
        )
        projectJsonFilePath = self._getProjectJsonFilePath(
            _pl.Path(mainWindow.projectFolder)
        )
        assert mainWindow.editor.massFlowSolver == "julia"

        mainWindow.editor.massFlowSolver = "type9352"
        mainWindow.editor.saveProject(showWarning=False)
        savedProjectJson = _json.loads(
            projectJsonFilePath.read_text(encoding="utf-8")
        )
        assert savedProjectJson["massFlowSolver"] == "type9352"

        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]
        mainWindow = _mw.MainWindow(  # type: ignore[attr-defined]
            logger, _prj.LoadProject(projectJsonFilePath)
        )
        qtbot.addWidget(mainWindow)
        assert mainWindow.editor.massFlowSolver == "type9352"

    def testMassFlowSolverMenu(self, qtbot, monkeypatch) -> None:
        testProject = self._getTestProjectByName("storage-tank")
        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow, _ = self._createMainWindowAndWarningHelper(
            helper, testProject.loadDiagramWarningOrNone, qtbot, monkeypatch
        )

        editor = mainWindow.editor
        assert editor.massFlowSolver == "julia"

        projectMenuActions = mainWindow.projectMenu.actions()
        massFlowSolverMenu = projectMenuActions[0].menu()
        assert massFlowSolverMenu is not None
        assert massFlowSolverMenu.title() == "Mass flow solver"
        assert projectMenuActions[1].isSeparator()

        solverActions = massFlowSolverMenu.actions()
        assert [a.text() for a in solverActions] == [
            "Julia (Type 4750)",
            "Type 9352",
        ]
        assert solverActions[0].isChecked()
        assert not solverActions[1].isChecked()

        editor.exportHydraulics(
            exportTo="ddck",
            massFlowSolver=editor.massFlowSolver,
            disableFileExistMsgb=True,
        )
        assert (
            helper.actualProjectFolderPath
            / "ddck"
            / "hydraulic"
            / "hydraulic.ddck"
        ).is_file()

        informationMessages = []

        def dummyInformation(_parent, title, text, *_ignored, **__ignored):
            informationMessages.append((title, text))
            return _qtw.QMessageBox.Ok

        monkeypatch.setattr(
            _qtw.QMessageBox,
            _qtw.QMessageBox.information.__name__,  # pylint: disable=no-member
            dummyInformation,
        )

        solverActions[1].trigger()

        assert editor.massFlowSolver == "type9352"
        assert not solverActions[0].isChecked()
        assert solverActions[1].isChecked()
        assert len(informationMessages) == 1
        assert "hydraulic.ddck" in informationMessages[0][1]

        # Triggering the already selected entry again changes nothing.
        solverActions[1].trigger()
        assert editor.massFlowSolver == "type9352"
        assert len(informationMessages) == 1

    def testExportHydraulicsPassesSolverThrough(
        self, qtbot, monkeypatch
    ) -> None:
        testProject = self._getTestProjectByName(
            "ex-hx-two-flow-solver-parameter-lines_complex_99"
        )
        helper = _th.Helper(testProject)
        helper.setup()

        mainWindow, _ = self._createMainWindowAndWarningHelper(
            helper, testProject.loadDiagramWarningOrNone, qtbot, monkeypatch
        )

        type9352Text = self._exportHydraulicsAndReadText(
            mainWindow.editor, "type9352"
        )
        juliaText = self._exportHydraulicsAndReadText(
            mainWindow.editor, "julia"
        )

        type9352Lines = self._getFlowSolverUnitText(type9352Text).splitlines()
        juliaLines = self._getFlowSolverUnitText(juliaText).splitlines()

        assert type9352Lines[0] == "UNIT 450 TYPE 9352"
        assert juliaLines[0] == "UNIT 450 TYPE 4750"

        nComponents = int(type9352Lines[5])
        assert type9352Lines[1] == f"PARAMETERS {4 + 4 * nComponents}"
        assert juliaLines[1] == f"PARAMETERS {5 + 4 * nComponents}"
        assert juliaLines[2] == f"{3 * nComponents} ! number of outputs: 3*N"

        type9352SourceLine = self._getComponentLine(
            type9352Text, "supplyWater"
        )
        juliaSourceLine = self._getComponentLine(juliaText, "supplyWater")
        assert _re.fullmatch(
            r"\d+ \d+ \d+ 6\s+!\d+ : supplyWater", type9352SourceLine
        )
        assert _re.fullmatch(
            r"\d+ \d+ \d+ 9\s+!\d+ : supplyWater", juliaSourceLine
        )

        assert "MfrsupplyWater" in type9352Text
        assert "MfrsupplyWater" not in juliaText

        assert "LABELS" not in type9352Text
        assert "LABELS 1\nMassFlowSolver\\MassFlowSolver.jl" in juliaText

    @staticmethod
    def _exportHydraulicsAndReadText(
        editor: _de.Editor, massFlowSolver  # type: ignore[name-defined]
    ) -> str:
        exportPath = editor.exportHydraulics(
            exportTo="ddck",
            massFlowSolver=massFlowSolver,
            disableFileExistMsgb=True,
        )
        return _pl.Path(exportPath).read_text(encoding="utf-8")

    @staticmethod
    def _getFlowSolverUnitText(deckText: str) -> str:
        start = deckText.index("UNIT 450 TYPE")
        end = deckText.index("INPUTS ", start)
        return deckText[start:end]

    @staticmethod
    def _getComponentLine(deckText: str, componentName: str) -> str:
        return next(
            line
            for line in deckText.splitlines()
            if f" : {componentName}" in line
        )

    @classmethod
    def _createMainWindowAndWarningHelper(
        cls,
        helper: _th.Helper,
        loadDiagramWarningOrNone: _th.LoadDiagramWarning | None,
        qtbot,
        monkeypatch,
    ) -> _tp.Tuple[_mw.MainWindow, _th.LoadDiagramWarningHelper]:  # type: ignore[name-defined]
        cls._configureDontAskWhetherWindowShouldBeClosed(monkeypatch)

        warningHelper = _th.LoadDiagramWarningHelper(loadDiagramWarningOrNone)

        monkeypatch.setattr(
            _qtw.QMessageBox,
            _qtw.QMessageBox.warning.__name__,  # pylint: disable=no-member
            warningHelper.warning,
        )

        projectFolderPath = helper.actualProjectFolderPath
        projectJsonFilePath = (
            projectFolderPath / f"{projectFolderPath.name}.json"
        )
        project = _prj.LoadProject(projectJsonFilePath)

        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

        mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

        warningHelper.verifyOrRaise()

        qtbot.addWidget(mainWindow)

        return mainWindow, warningHelper

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
        singlePipeConnections = [
            o
            for o in blockItemsAndConnections
            if isinstance(o, _spc.SinglePipeConnection)
        ]
        valves = [
            o for o in blockItemsAndConnections if isinstance(o, _tv.TVentil)
        ]

        for singlePipeConnection in singlePipeConnections:
            singlePipeConnection.massFlowLabel.setPlainText("")

        for valve in valves:
            valve.posLabel.setPlainText("")

        massFlowSolverVisualizer = _mfv.MassFlowVisualizer(  # type: ignore[attr-defined]  # pylint: disable=unused-variable
            mainWindow, massFlowRatesPrintFilePath, temperaturesPrintFilePath
        )

        areAllMassFlowLabelsSet = all(
            c.massFlowLabel.toPlainText() for c in singlePipeConnections
        )
        areAllValvePositionLabelsSet = all(
            v.posLabel.toPlainText() for v in valves
        )
        assert areAllMassFlowLabelsSet and areAllValvePositionLabelsSet

    def _exportMassFlowSolverDeckAndRunTrnsys(self, editor: _de.Editor):  # type: ignore[name-defined]
        # Type 9352 is passed explicitly, so that the CI runner doesn't need
        # julia4trnsys and the Type 9352 export stays covered (see #649).
        exportedFilePath = self._exportHydraulic(
            editor, _format="mfs", massFlowSolver="type9352"
        )

        trnExePath = self._getTrnExePath()

        _sp.run([str(trnExePath), str(exportedFilePath), "/H"], check=True)

    @staticmethod
    def _getTrnExePath():
        isRunDuringCi = _os.environ.get("CI") == "true"
        if isRunDuringCi:
            return _pl.PureWindowsPath(
                r"C:\CI-Programs\TRNSYS18_pytrnsys\Exe\TrnEXE.exe"
            )

        return _pl.PureWindowsPath(r"C:\TRNSYS18\Exe\TrnEXE.exe")

    @classmethod
    def _exportHydraulic(
        cls, editor: _de.Editor, *, _format, massFlowSolver  # type: ignore[name-defined]
    ) -> str:  # type: ignore[name-defined]
        exportedFilePath = editor.exportHydraulics(
            exportTo=_format, massFlowSolver=massFlowSolver
        )
        return exportedFilePath

    @_pt.mark.tool
    @_pt.mark.skip(
        "This test is really a script to be run by the user from the IDE to update the expected files."
    )
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testToolUpdateExportDeckExpectedFiles(
        self, testProject: _th.Project, qtbot, monkeypatch
    ) -> None:
        shallComparisonsAlwaysSucceed = True
        self.testExportDeck(
            testProject, qtbot, monkeypatch, shallComparisonsAlwaysSucceed
        )

        self._updateExpectedFiles(testProject)

    @_pt.mark.tool
    @_pt.mark.skip(
        "This test is really a script to be run by the user from the IDE to update the expected files."
    )
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testToolUpdateMassFlowSolverExpectedFiles(
        self, testProject: _th.Project, qtbot, monkeypatch
    ) -> None:
        shallComparisonsAlwaysSucceed = True
        self.testMassFlowSolver(
            testProject, qtbot, monkeypatch, shallComparisonsAlwaysSucceed
        )

        self._updateExpectedFiles(testProject)

    def _updateExpectedFiles(self, testProject):
        helper = _th.Helper(testProject)
        _su.copytree(
            helper.actualProjectFolderPath,
            helper.expectedProjectFolderPath,
            dirs_exist_ok=True,
        )
        self._resetHardCodedPathsInDeckFile(testProject, helper)

    def _resetHardCodedPathsInDeckFile(
        self, project: _th.Project, helper: _th.Helper
    ) -> None:
        deckFileName = f"{project.projectName}.dck"
        relativeDeckFilePath: str | _pl.Path = (
            project.resultsDirPathOrNone / deckFileName
            if project.resultsDirPathOrNone
            else deckFileName
        )
        deckFilePath = helper.expectedProjectFolderPath / relativeDeckFilePath
        (
            hardcodedPathInExpectedDeck,
            hardCodedPathInActualDeck,
        ) = self._getHardCodedPathPrefixesForReplacingInExpectedDeck()
        deckFileContent = deckFilePath.read_text(encoding="windows-1252")
        updatedDeckFileContent = deckFileContent.replace(
            hardCodedPathInActualDeck, hardcodedPathInExpectedDeck
        )
        deckFilePath.write_text(
            updatedDeckFileContent, encoding="windows-1252"
        )
