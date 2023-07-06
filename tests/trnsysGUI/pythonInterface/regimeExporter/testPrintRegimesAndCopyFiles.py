import dataclasses as _dc
import os as _os
import pathlib as _pl
import typing as _tp
import matplotlib.testing.compare as _mpltc  # type: ignore[import]

import pytrnsys.utils.log as _ulog

import trnsysGUI as _GUI
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj
import trnsysGUI.pythonInterface.regimeExporter.renderDiagramOnPDFfromPython as _rdopfp

_PROJECT_NAME = "diagramForRegimes"
_BASE_FOLDER_FILE_PATH = "..\\tests\\trnsysGUI\\data\\"
_EXPECTED_FILES_PATH = "expectedPDFs"
_RESULTS_DIR_NAME = "results"
_RESULTS_DIR_NAME_2 = "resultsReducedUsage"
_REGIMES_FILENAME = "regimes.csv"


@_dc.dataclass
class PathFinder:  # pylint: disable=too-many-instance-attributes
    projectName: str
    baseFolderRelativePath: str
    expectedFolderName: str
    resultsFolderName: str
    resultsFolderName2: _tp.Optional[str]
    fileEnding: str = _dc.field(init=False)
    pdfName: str = _dc.field(init=False)
    svgName: str = _dc.field(init=False)

    @property
    def projectDir(self):
        return _pl.Path(_GUI.__file__).parent / self.baseFolderRelativePath / self.projectName

    @property
    def expectedFilesDir(self):
        return self.projectDir / self.expectedFolderName

    @property
    def resultsDir(self):
        return self.projectDir / self.resultsFolderName

    @property
    def resultsDir2(self):
        return self.projectDir / self.resultsFolderName2

    def setFileEnding(self, fileEnding):
        self.fileEnding = fileEnding
        self._setPdfName()
        self._setSvgName()

    def _setPdfName(self):
        self.pdfName = self.projectName + self.fileEnding + ".pdf"

    def _setSvgName(self):
        self.svgName = self.projectName + self.fileEnding + ".svg"

    @property
    def expectedPdfPath(self):
        return self.expectedFilesDir / self.pdfName

    @property
    def newPdfPath(self):
        return self.projectDir / self.resultsDir / self.pdfName

    @property
    def alternatePdfPath(self):
        return self.projectDir / self.resultsDir2 / self.pdfName

    @property
    def expectedSvgPath(self):
        return self.expectedFilesDir / self.svgName

    @property
    def newSvgPath(self):
        return self.projectDir / self.resultsDir / self.svgName

    @property
    def alternateSvgPath(self):
        return self.projectDir / self.resultsDir2 / self.svgName


pathFinder = PathFinder(
    _PROJECT_NAME, _BASE_FOLDER_FILE_PATH, _EXPECTED_FILES_PATH, _RESULTS_DIR_NAME, _RESULTS_DIR_NAME_2
)


_DATA_DIR = pathFinder.projectDir
_RESULTS_DIR = pathFinder.resultsDir
_RESULTS_DIR_2 = pathFinder.resultsDir2


def _ensureDirExists(dirPath):
    if not _os.path.isdir(dirPath):
        _os.makedirs(dirPath)


_ensureDirExists(_RESULTS_DIR)
_ensureDirExists(_RESULTS_DIR_2)


pathFinder.setFileEnding("_diagram")
_EXPECTED_DIAGRAM_PATH = pathFinder.expectedPdfPath
_NEW_DIAGRAM_PATH = pathFinder.newPdfPath
_NEW_DIAGRAM_PATH_2 = pathFinder.alternatePdfPath

pathFinder.setFileEnding("_name1")
_EXPECTED_NAME1_PATH = pathFinder.expectedPdfPath
_NEW_NAME1_PATH = pathFinder.newPdfPath
_NEW_NAME1_PATH_2 = pathFinder.alternatePdfPath
_EXPECTED_NAME1_SVG_PATH = pathFinder.expectedSvgPath
_NEW_NAME1_SVG_PATH = pathFinder.newSvgPath
_NEW_NAME1_SVG_PATH_2 = pathFinder.alternateSvgPath

pathFinder.setFileEnding("_name2")
_EXPECTED_NAME2_PATH = pathFinder.expectedPdfPath
_NEW_NAME2_PATH = pathFinder.newPdfPath
_NEW_NAME2_PATH_2 = pathFinder.alternatePdfPath


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
        regimeEnding = "_dummy_regime"

        pathFinder2 = PathFinder(
            projectName, _BASE_FOLDER_FILE_PATH, _EXPECTED_FILES_PATH, _RESULTS_DIR_NAME, _RESULTS_DIR_NAME_2
        )
        dataDir = pathFinder2.projectDir
        resultsDir = pathFinder2.resultsDir

        _ensureDirExists(resultsDir)

        pathFinder2.setFileEnding(regimeEnding)

        mainWindow = _createMainWindow(dataDir, projectName, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(projectName, dataDir, resultsDir, _REGIMES_FILENAME, mainWindow)
        regimeExporter.export(pumpTapPairs=pumpTapPairs, onlyTheseRegimes=onlyTheseRegimes)

        self._fileExistsAndIsCorrect(pathFinder2.newPdfPath, pathFinder2.expectedPdfPath)

        pathFinder2.setFileEnding("_diagram")
        assert not pathFinder2.newPdfPath.is_file()


# non-qtbot solution?
