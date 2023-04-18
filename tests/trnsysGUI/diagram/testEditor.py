import dataclasses as _dc
import os as _os
import pathlib as _pl
import shutil as _su
import subprocess as _sp
import time as _time
import typing as _tp

import PyQt5.QtWidgets as _qtw
import pandas as _pd
import pytest as _pt


import pytrnsys.utils.log as _ulog

import trnsysGUI.MassFlowVisualizer as _mfv
import trnsysGUI.TVentil as _tv
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.diagram.Editor as _de
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj
import trnsysGUI.storageTank.widget as _stw

_DATA_DIR = _pl.Path(__file__).parent / "data"


@_dc.dataclass
class _Project:
    projectName: str
    testCasesDirName: str
    exampleDirNameToCopyFrom: _tp.Optional[str] = None

    @staticmethod
    def createForTestProject(projectName: str) -> "_Project":
        return _Project(projectName, "tests")

    @staticmethod
    def createForExampleProject(projectName: str, exampleDirNameToCopyFrom: str = "examples") -> "_Project":
        return _Project(projectName, "examples", exampleDirNameToCopyFrom)

    @property
    def testId(self) -> str:
        return f"{self.testCasesDirName}/{self.projectName}"


def getProjects() -> _tp.Iterable[_Project]:
    yield _Project.createForExampleProject("TRIHP_dualSource", exampleDirNameToCopyFrom="examplesToBeCompleted")
    yield _Project.createForExampleProject("icegrid")

    yield from getTestProjects()


def getTestProjects() -> _tp.Iterable[_Project]:
    testProjectTestCasesDir = _DATA_DIR / "tests"
    testProjectTestCaseDirPaths = [tc for tc in testProjectTestCasesDir.iterdir() if tc.name != "README.txt"]
    for testProjectTestCaseDirPath in testProjectTestCaseDirPaths:
        projectName = testProjectTestCaseDirPath.name
        yield _Project.createForTestProject(projectName)


TEST_CASES = [_pt.param(p, id=p.testId) for p in getProjects()]


class TestEditor:
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testExportDeck(self, testProject: _Project, qtbot, monkeypatch) -> None:
        helper = _Helper(testProject)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)
        editor = mainWindow.editor

        monkeypatch.chdir(helper.actualProjectFolderPath)

        self.exportAndTestStorageDdckFiles(editor, helper)

        self._exportAndTestHydraulicDdckFile(editor, helper)

        self._exportAndTestPlaceholdersJsonAndDeckFile(mainWindow, testProject, helper, monkeypatch)

    def exportAndTestStorageDdckFiles(self, editor, helper):
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

    def _exportAndTestPlaceholdersJsonAndDeckFile(self, mainWindow, testProject, helper, monkeypatch):
        def dummyInformation(*_, **__):
            return _qtw.QMessageBox.Ok

        monkeypatch.setattr(
            _qtw.QMessageBox, _qtw.QMessageBox.information.__name__, dummyInformation  # pylint: disable=no-member
        )

        mainWindow.exportDck()
        helper.ensureFilesAreEqual("DdckPlaceHolderValues.json")

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
        self, testProject: _Project, qtbot, monkeypatch
    ) -> None:  # pylint: disable=too-many-locals
        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

        helper = _Helper(testProject)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)

        convertedProjectFolderPath = helper.actualProjectFolderPath.parent / "converted"
        while convertedProjectFolderPath.exists():
            _su.rmtree(convertedProjectFolderPath)
            _time.sleep(0.5)
        _os.mkdir(convertedProjectFolderPath)

        mainWindow.copyContentsToNewFolder(convertedProjectFolderPath, helper.actualProjectFolderPath)

        convertedJsonFilePath = convertedProjectFolderPath / f"{convertedProjectFolderPath.name}.json"
        convertedProject = _prj.LoadProject(convertedJsonFilePath)
        _mw.MainWindow(logger, convertedProject)  # type: ignore[attr-defined]

    @_pt.mark.needs_trnsys
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testMassFlowSolver(self, testProject: _Project, qtbot, monkeypatch) -> None:
        helper = _Helper(testProject)
        helper.setup()

        mainWindow = self._createMainWindow(helper, qtbot, monkeypatch)

        self._exportMassFlowSolverDeckAndRunTrnsys(mainWindow.editor)

        massFlowSolverDeckFileName = f"{testProject.projectName}_mfs.dck"
        helper.ensureFilesAreEqual(massFlowSolverDeckFileName)

        massFlowRatesPrintFileName = f"{testProject.projectName}_Mfr.prt"
        helper.ensureCSVsAreEqual(massFlowRatesPrintFileName)

        temperaturesPintFileName = f"{testProject.projectName}_T.prt"
        helper.ensureCSVsAreEqual(temperaturesPintFileName)

        massFlowRatesPrintFilePath = helper.actualProjectFolderPath / massFlowRatesPrintFileName
        temperaturesPrintFilePath = helper.actualProjectFolderPath / temperaturesPintFileName
        self._assertMassFlowVisualizerLoadsData(massFlowRatesPrintFilePath, temperaturesPrintFilePath, mainWindow)

    @staticmethod
    def _createMainWindow(helper, qtbot, monkeypatch):
        monkeypatch.setattr(
            _mw.MainWindow,  # type: ignore[attr-defined]
            _mw.MainWindow.closeEvent.__name__,  # type: ignore[attr-defined]
            _patchedCloseEvent,
        )

        projectFolderPath = helper.actualProjectFolderPath
        projectJsonFilePath = projectFolderPath / f"{projectFolderPath.name}.json"
        project = _prj.LoadProject(projectJsonFilePath)

        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

        mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

        qtbot.addWidget(mainWindow)

        return mainWindow

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
            firstSegment = singlePipeConnection.firstS
            assert firstSegment

            firstSegment.labelMass.setPlainText("")

        for valve in valves:
            valve.posLabel.setPlainText("")

        massFlowSolverVisualizer = _mfv.MassFlowVisualizer(  # type: ignore[attr-defined]  # pylint: disable=unused-variable
            mainWindow, massFlowRatesPrintFilePath, temperaturesPrintFilePath
        )

        areAllMassFlowLabelsSet = all(s.firstS and s.firstS.labelMass.toPlainText() for s in singlePipeConnections)
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


def _patchedCloseEvent(_, closeEvent):
    return closeEvent.accept()


class _Helper:
    def __init__(
        self,
        project: _Project,
    ):
        self._project = project

        testCasesFolderPath = _DATA_DIR / self._project.testCasesDirName

        # project name is used twice because the project file must always be contained in a folder
        # of the same name
        self.actualProjectFolderPath = testCasesFolderPath / self._project.projectName / self._project.projectName

        self._expectedProjectFolderPath = testCasesFolderPath / self._project.projectName / "expected"

    def setup(self):
        if self._project.exampleDirNameToCopyFrom:
            self._copyExampleToTestInputFolder()

        self._removeGeneratedFiles()

    def _removeGeneratedFiles(self):
        for child in self.actualProjectFolderPath.iterdir():
            if child.name in ("ddck", f"{self._project.projectName}.json", "run.config"):
                continue

            if child.is_dir():
                _su.rmtree(child)
            else:
                child.unlink()

    def ensureFilesAreEqual(
        self, fileRelativePathAsString: str, replaceInExpected: _tp.Optional[_tp.Tuple[str, str]] = None
    ) -> None:
        actualFilePath, expectedFilePath = self._getActualAndExpectedFilePath(fileRelativePathAsString)

        actualContent = actualFilePath.read_text()

        expectedContent = expectedFilePath.read_text(encoding="windows-1252")
        if replaceInExpected:
            old, new = replaceInExpected
            expectedContent = expectedContent.replace(old, new)

        assert actualContent == expectedContent

    def _getActualAndExpectedFilePath(self, fileRelativePathAsString):
        fileRelativePath = _pl.Path(fileRelativePathAsString)
        actualFilePath = self.actualProjectFolderPath / fileRelativePath
        expectedFilePath = self._expectedProjectFolderPath / fileRelativePath
        return actualFilePath, expectedFilePath

    def ensureCSVsAreEqual(self, fileRelativePathAsString: str, absoluteTolerance: float = 1e-10) -> None:
        actualFilePath, expectedFilePath = self._getActualAndExpectedFilePath(fileRelativePathAsString)

        actualDf: _pd.DataFrame = _pd.read_csv(actualFilePath, delim_whitespace=True)
        expectedDf: _pd.DataFrame = _pd.read_csv(expectedFilePath, delim_whitespace=True)

        assert actualDf.shape == expectedDf.shape

        actualColumns = "\n".join(sorted(actualDf.columns))  # pylint: disable=no-member
        expectedColumns = "\n".join(sorted(expectedDf.columns))  # pylint: disable=no-member

        assert actualColumns == expectedColumns

        maxAbsoluteDifference = (actualDf - expectedDf).max().max()

        assert maxAbsoluteDifference <= absoluteTolerance

    def _copyExampleToTestInputFolder(self):
        if self.actualProjectFolderPath.exists():
            _su.rmtree(self.actualProjectFolderPath)

        pytrnsysGuiDir = _pl.Path(__file__).parents[3]
        exampleFolderPath = pytrnsysGuiDir / "data" / self._project.exampleDirNameToCopyFrom / self._project.projectName

        _su.copytree(exampleFolderPath, self.actualProjectFolderPath)
