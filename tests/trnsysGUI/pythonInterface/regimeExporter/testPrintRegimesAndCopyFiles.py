import os as _os
import pathlib as _pl
import matplotlib.testing.compare as _mpltc  # type: ignore[import]

import pytrnsys.utils.log as _ulog

import trnsysGUI as _GUI
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj
import trnsysGUI.pythonInterface.regimeExporter.renderDiagramOnPDFfromPython as _rdopfp

_PROJECT_NAME = "diagramForRegimes"
_DATA_DIR = _pl.Path(_GUI.__file__).parent / f"..\\tests\\trnsysGUI\\data\\{_PROJECT_NAME}"
_REGIMES_FILENAME = "regimes.csv"
_EXPECTED_PDFS_DIR = _DATA_DIR / "expectedPDFs"
_RESULTS_DIR = _DATA_DIR / "results"
_RESULTS_DIR_2 = _DATA_DIR / "resultsReducedUsage"

_DIAGRAM_ENDING = "_diagram.pdf"
_NAME1_ENDING = "_name1.pdf"
_NAME2_ENDING = "_name2.pdf"
_NAME1_SVG_ENDING = "_name1.svg"


def _ensureDirExists(dirPath):
    if not _os.path.isdir(dirPath):
        _os.makedirs(dirPath)


_ensureDirExists(_RESULTS_DIR)
_ensureDirExists(_RESULTS_DIR_2)


def _getExpectedAndNewFilePaths(ending, resultsDir):
    pdfName = _PROJECT_NAME + ending
    expectedPdfPath = _EXPECTED_PDFS_DIR / pdfName
    newPdfPath = _DATA_DIR / resultsDir / pdfName
    return expectedPdfPath, newPdfPath


_EXPECTED_DIAGRAM_PATH, _NEW_DIAGRAM_PATH = _getExpectedAndNewFilePaths(_DIAGRAM_ENDING, _RESULTS_DIR)
_EXPECTED_NAME1_PATH, _NEW_NAME1_PATH = _getExpectedAndNewFilePaths(_NAME1_ENDING, _RESULTS_DIR)
_EXPECTED_NAME2_PATH, _NEW_NAME2_PATH = _getExpectedAndNewFilePaths(_NAME2_ENDING, _RESULTS_DIR)
_EXPECTED_NAME1_SVG_PATH, _NEW_NAME1_SVG_PATH = _getExpectedAndNewFilePaths(_NAME1_SVG_ENDING, _RESULTS_DIR)

_, _NEW_DIAGRAM_PATH_2 = _getExpectedAndNewFilePaths(_DIAGRAM_ENDING, _RESULTS_DIR_2)
_, _NEW_NAME1_PATH_2 = _getExpectedAndNewFilePaths(_NAME1_ENDING, _RESULTS_DIR_2)
_, _NEW_NAME2_PATH_2 = _getExpectedAndNewFilePaths(_NAME2_ENDING, _RESULTS_DIR_2)
_, _NEW_NAME1_SVG_PATH_2 = _getExpectedAndNewFilePaths(_NAME1_SVG_ENDING, _RESULTS_DIR_2)


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


# non-qtbot solution?
