import dataclasses as _dc
import os as _os
import matplotlib.testing.compare as _mpltc  # type: ignore[import]
import pathlib as _pl
import typing as _tp

import pytrnsys.utils.log as _ulog

import trnsysGUI as _GUI
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj
import trnsysGUI.pythonInterface.regimeExporter.renderDiagramOnPDFfromPython as _rdopfp

_PROJECT_NAME = "diagramForRegimes"
baseFolderRelativePath = "..\\tests\\trnsysGUI\\data\\"
expectedFolderName = "expectedPDFs"
resultsDirName = "results"
resultsDirName2 = "resultsReducedUsage"
_REGIMES_FILENAME = "regimes.csv"


@_dc.dataclass
class PathFinder:
    projectName: str
    baseFolderRelativePath: str
    expectedFolderName: str
    resultsFolderName: str
    resultsFolderName2: _tp.Optional[str]

    @property
    def dataDir(self):
        return _pl.Path(_GUI.__file__).parent / self.baseFolderRelativePath / self.projectName

    @property
    def expectedPdfsDir(self):
        return self.dataDir / self.expectedFolderName

    @property
    def resultsDir(self):
        return self.dataDir / self.resultsFolderName

    @property
    def resultsDir2(self):
        return self.dataDir / self.resultsFolderName2


pathFinder = PathFinder(_PROJECT_NAME, baseFolderRelativePath, expectedFolderName, resultsDirName, resultsDirName2)


_DATA_DIR = pathFinder.dataDir
_EXPECTED_PDFS_DIR = pathFinder.expectedPdfsDir
_RESULTS_DIR = pathFinder.resultsDir
_RESULTS_DIR_2 = pathFinder.resultsDir2

_DIAGRAM_ENDING = "_diagram.pdf"
_NAME1_ENDING = "_name1.pdf"
_NAME2_ENDING = "_name2.pdf"
_NAME1_SVG_ENDING = "_name1.svg"


def _ensureDirExists(dirPath):
    if not _os.path.isdir(dirPath):
        _os.makedirs(dirPath)


_ensureDirExists(_RESULTS_DIR)
_ensureDirExists(_RESULTS_DIR_2)


def _getExpectedAndNewFilePaths(ending, resultsDir, dataDir, projectName, expectedPdfsDir):
    pdfName = projectName + ending
    expectedPdfPath = expectedPdfsDir / pdfName
    newPdfPath = dataDir / resultsDir / pdfName
    return expectedPdfPath, newPdfPath


_EXPECTED_DIAGRAM_PATH, _NEW_DIAGRAM_PATH = _getExpectedAndNewFilePaths(
    _DIAGRAM_ENDING, _RESULTS_DIR, _DATA_DIR, _PROJECT_NAME, _EXPECTED_PDFS_DIR
)
_EXPECTED_NAME1_PATH, _NEW_NAME1_PATH = _getExpectedAndNewFilePaths(
    _NAME1_ENDING, _RESULTS_DIR, _DATA_DIR, _PROJECT_NAME, _EXPECTED_PDFS_DIR
)
_EXPECTED_NAME2_PATH, _NEW_NAME2_PATH = _getExpectedAndNewFilePaths(
    _NAME2_ENDING, _RESULTS_DIR, _DATA_DIR, _PROJECT_NAME, _EXPECTED_PDFS_DIR
)
_EXPECTED_NAME1_SVG_PATH, _NEW_NAME1_SVG_PATH = _getExpectedAndNewFilePaths(
    _NAME1_SVG_ENDING, _RESULTS_DIR, _DATA_DIR, _PROJECT_NAME, _EXPECTED_PDFS_DIR
)

_, _NEW_DIAGRAM_PATH_2 = _getExpectedAndNewFilePaths(
    _DIAGRAM_ENDING, _RESULTS_DIR_2, _DATA_DIR, _PROJECT_NAME, _EXPECTED_PDFS_DIR
)
_, _NEW_NAME1_PATH_2 = _getExpectedAndNewFilePaths(
    _NAME1_ENDING, _RESULTS_DIR_2, _DATA_DIR, _PROJECT_NAME, _EXPECTED_PDFS_DIR
)
_, _NEW_NAME2_PATH_2 = _getExpectedAndNewFilePaths(
    _NAME2_ENDING, _RESULTS_DIR_2, _DATA_DIR, _PROJECT_NAME, _EXPECTED_PDFS_DIR
)
_, _NEW_NAME1_SVG_PATH_2 = _getExpectedAndNewFilePaths(
    _NAME1_SVG_ENDING, _RESULTS_DIR_2, _DATA_DIR, _PROJECT_NAME, _EXPECTED_PDFS_DIR
)


def _createMainWindow(projectFolder, projectName, qtbot):
    projectJsonFilePath = projectFolder / f"{projectName}.json"
    project = _prj.LoadProject(projectJsonFilePath)

    logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

    mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

    qtbot.addWidget(mainWindow)
    mainWindow.showBoxOnClose = False
    mainWindow.editor.forceOverwrite = True

    return mainWindow


class TestPrintRegimesAndCopyFiles:
    def testMplInstallation(self):
        assert "pdf" in _mpltc.comparable_formats()
        assert "svg" in _mpltc.comparable_formats()

    def testUsingQtBot(self, qtbot):
        mainWindow = _createMainWindow(_DATA_DIR, _PROJECT_NAME, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(_PROJECT_NAME, _DATA_DIR, _RESULTS_DIR, _REGIMES_FILENAME, mainWindow)
        regimeExporter.export()

        self._fileExistsAndIsCorrect(_NEW_DIAGRAM_PATH, _EXPECTED_DIAGRAM_PATH)
        self._fileExistsAndIsCorrect(_NEW_NAME1_PATH, _EXPECTED_NAME1_PATH)
        self._fileExistsAndIsCorrect(_NEW_NAME1_SVG_PATH, _EXPECTED_NAME1_SVG_PATH)
        self._fileExistsAndIsCorrect(_NEW_NAME2_PATH, _EXPECTED_NAME2_PATH)

    @staticmethod
    def _fileExistsAndIsCorrect(producedFile, expectedFile):
        assert producedFile.is_file()
        _mpltc.compare_images(str(producedFile), str(expectedFile), 0, in_decorator=False)

    def testUsingQtBotForGivenRegimes(self, qtbot):
        onlyTheseRegimes = ["name1"]
        mainWindow = _createMainWindow(_DATA_DIR, _PROJECT_NAME, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(_PROJECT_NAME, _DATA_DIR, _RESULTS_DIR_2, _REGIMES_FILENAME, mainWindow)
        regimeExporter.export(onlyTheseRegimes=onlyTheseRegimes)

        self._fileExistsAndIsCorrect(_NEW_NAME1_PATH_2, _EXPECTED_NAME1_PATH)
        self._fileExistsAndIsCorrect(_NEW_NAME1_PATH_2, _EXPECTED_DIAGRAM_PATH)
        assert not _NEW_DIAGRAM_PATH_2.is_file()
        assert not _NEW_NAME2_PATH_2.is_file()

    def testUsingQtBotForRegimeWithTap(self, qtbot):
        pumpTapPairs = {"Pump5": "WtSp1"}
        onlyTheseRegimes = ["dummy_regime"]
        projectName = "diagramWithTapForRegimes"

        pathFinder2 = PathFinder(
            projectName, baseFolderRelativePath, expectedFolderName, resultsDirName, resultsDirName2
        )
        dataDir = pathFinder2.dataDir
        expectedPdfsDir = pathFinder2.expectedPdfsDir
        resultsDir = pathFinder2.resultsDir

        _ensureDirExists(resultsDir)

        _, newDiagramPath = _getExpectedAndNewFilePaths(
            _DIAGRAM_ENDING, resultsDir, dataDir, projectName, expectedPdfsDir
        )
        regimeEnding = "_dummy_regime.pdf"
        expectedFilePath, newFilePath = _getExpectedAndNewFilePaths(
            regimeEnding, resultsDir, dataDir, projectName, expectedPdfsDir
        )

        mainWindow = _createMainWindow(dataDir, projectName, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(projectName, dataDir, resultsDir, _REGIMES_FILENAME, mainWindow)
        regimeExporter.export(pumpTapPairs=pumpTapPairs, onlyTheseRegimes=onlyTheseRegimes)

        self._fileExistsAndIsCorrect(newFilePath, expectedFilePath)

        assert not newDiagramPath.is_file()


# non-qtbot solution?
