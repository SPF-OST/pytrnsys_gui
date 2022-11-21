import dataclasses as _dc
import logging as _log
import os as _os
import pathlib as _pl
import shutil as _su
import subprocess as _sp
import sys as _sys
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
    shallCopyFolderFromExamples: bool

    @staticmethod
    def createForTestProject(projectName: str) -> "_Project":
        return _Project(projectName, "tests", False)

    @staticmethod
    def createForExampleProject(projectName: str) -> "_Project":
        return _Project(projectName, "examples", True)

    @property
    def testId(self) -> str:
        return f"{self.testCasesDirName}/{self.projectName}"


def getProjects() -> _tp.Iterable[_Project]:
    yield _Project.createForExampleProject("TRIHP_dualSource")

    yield from getTestProjects()


def getTestProjects() -> _tp.Iterable[_Project]:
    testProjectTestCasesDir = _DATA_DIR / "tests"
    testProjectTestCaseDirPaths = [tc for tc in testProjectTestCasesDir.iterdir() if tc.name != "README.txt"]
    for testProjectTestCaseDirPath in testProjectTestCaseDirPaths:
        projectName = testProjectTestCaseDirPath.name
        yield _Project.createForTestProject(projectName)


TEST_CASES = [_pt.param(p, id=p.testId) for p in getProjects()]


class TestEditor:
    @_pt.mark.parametrize("project", TEST_CASES)
    def testStorageAndHydraulicExports(  # pylint: disable=too-many-locals
        self, project: _Project, request: _pt.FixtureRequest
    ) -> None:
        helper = _Helper(project)
        helper.setup()

        # The following line is required otherwise QT will crash
        application = _qtw.QApplication([])

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        projectFolderPath = helper.actualProjectFolderPath

        editor = self._createEditor(projectFolderPath)
        editor.exportHydraulics(exportTo="mfs")
        mfsDdckRelativePath = f"{project.projectName}_mfs.dck"
        helper.ensureFilesAreEqual(mfsDdckRelativePath)

        storageTankNames = self._exportStorageTanksAndGetNames(editor)
        for storageTankName in storageTankNames:
            ddckFileRelativePath = f"ddck/{storageTankName}/{storageTankName}.ddck"
            helper.ensureFilesAreEqual(ddckFileRelativePath)

        editor.exportHydraulics(exportTo="ddck")
        hydraulicDdckRelativePath = "ddck/hydraulic/hydraulic.ddck"
        helper.ensureFilesAreEqual(hydraulicDdckRelativePath)

        editor.exportDdckPlaceHolderValuesJsonFile(shallShowMessageOnSuccess=False)
        helper.ensureFilesAreEqual("DdckPlaceHolderValues.json")

    @classmethod
    def _exportStorageTanksAndGetNames(cls, editor: _de.Editor) -> _tp.Sequence[str]:  # type: ignore[name-defined]
        storageTanks = [o for o in editor.trnsysObj if isinstance(o, _stw.StorageTank)]  # pylint: disable=no-member

        for storageTank in storageTanks:
            storageTank.exportDck()

        storageTankNames = [t.displayName for t in storageTanks]

        return storageTankNames

    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testSaveAndReloadProject(  # pylint: disable=too-many-locals
        self, testProject: _Project, request: _pt.FixtureRequest
    ) -> None:
        # The following line is required otherwise QT will crash
        application = _qtw.QApplication([])

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        logger = _ulog.setup_custom_logger("root", "DEBUG")  # type: ignore[attr-defined]

        helper = _Helper(testProject)
        helper.setup()

        jsonFilePath = helper.actualProjectFolderPath / f"{helper.actualProjectFolderPath.name}.json"
        project = _prj.LoadProject(jsonFilePath)
        mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

        convertedProjectFolderPath = helper.actualProjectFolderPath.parent / "converted"
        while convertedProjectFolderPath.exists():
            _su.rmtree(convertedProjectFolderPath)
            _time.sleep(0.5)
        _os.mkdir(convertedProjectFolderPath)

        mainWindow.copyContentsToNewFolder(convertedProjectFolderPath, helper.actualProjectFolderPath)

        convertedJsonFilePath = convertedProjectFolderPath / f"{convertedProjectFolderPath.name}.json"
        convertedProject = _prj.LoadProject(convertedJsonFilePath)
        _mw.MainWindow(logger, convertedProject)  # type: ignore[attr-defined]

    @_pt.mark.linux_ci
    @_pt.mark.parametrize("testProject", TEST_CASES)
    def testMassFlowSolver(self, testProject: _Project, request: _pt.FixtureRequest) -> None:
        helper = _Helper(testProject)
        helper.setup()

        # The following line is required otherwise QT will crash
        application = _qtw.QApplication([])

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        projectFolderPath = helper.actualProjectFolderPath
        projectJsonFilePath = projectFolderPath / f"{projectFolderPath.name}.json"
        project = _prj.LoadProject(projectJsonFilePath)
        logger = _ulog.setup_custom_logger("root", "DEBUG")  # type: ignore[attr-defined]
        mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

        self._exportMassFlowSolverDeckAndRunTrnsys(mainWindow.centralWidget)

        massFlowRatesPrintFileName = f"{testProject.projectName}_Mfr.prt"
        helper.ensureCSVsAreEqual(massFlowRatesPrintFileName)

        temperaturesPintFileName = f"{testProject.projectName}_T.prt"
        helper.ensureCSVsAreEqual(temperaturesPintFileName)

        massFlowRatesPrintFilePath = helper.actualProjectFolderPath / massFlowRatesPrintFileName
        temperaturesPrintFilePath = helper.actualProjectFolderPath / temperaturesPintFileName
        self._assertMassFlowVisualizerLoadsData(massFlowRatesPrintFilePath, temperaturesPrintFilePath, mainWindow)

    @staticmethod
    def _assertMassFlowVisualizerLoadsData(
        massFlowRatesPrintFilePath: _pl.Path,
        temperaturesPrintFilePath: _pl.Path,
        mainWindow: _mw.MainWindow,  # type: ignore[name-defined]
    ):
        blockItemsAndConnections = mainWindow.centralWidget.trnsysObj
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

        trnsysExePath = _pl.PureWindowsPath(r"C:\TRNSYS18\Exe\TrnExe.exe")

        runningOnWindows = _sys.platform.startswith("win32")
        if runningOnWindows:
            _sp.run([str(trnsysExePath), str(exportedFilePath), "/H"], check=True)
            return

        # Running on Linux using Wine
        zDrivePath = _pl.PureWindowsPath("Z:")
        exportedFileWindowswPath = zDrivePath / exportedFilePath

        _sp.run(["wine", str(trnsysExePath), str(exportedFileWindowswPath), "/H"], check=True)

    @classmethod
    def _exportHydraulic(cls, editor: _de.Editor, *, _format) -> str:  # type: ignore[name-defined]
        exportedFilePath = editor.exportHydraulics(exportTo=_format)
        return exportedFilePath

    @staticmethod
    def _createEditor(projectFolderPath):
        logger = _log.Logger("root")
        editor = _de.Editor(
            parent=None,
            projectFolder=str(projectFolderPath),
            jsonPath=None,
            loadValue="load",
            logger=logger,
        )
        return editor


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
        if self._project.shallCopyFolderFromExamples:
            self._copyExampleToTestInputFolder()

        self._removeGeneratedFiles()

    def _removeGeneratedFiles(self):
        for child in self.actualProjectFolderPath.iterdir():
            if child.name in ("ddck", f"{self._project.projectName}.json"):
                continue

            if child.is_dir():
                _su.rmtree(child)
            else:
                child.unlink()

    def ensureFilesAreEqual(self, fileRelativePathAsString: str) -> None:
        actualFilePath, expectedFilePath = self._getActualAndExpectedFilePath(fileRelativePathAsString)
        actualContent = actualFilePath.read_text()
        expectedContent = expectedFilePath.read_text(encoding="windows-1252")

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
        exampleFolderPath = pytrnsysGuiDir / "data" / "examplesToBeCompleted" / self._project.projectName

        _su.copytree(exampleFolderPath, self.actualProjectFolderPath)
