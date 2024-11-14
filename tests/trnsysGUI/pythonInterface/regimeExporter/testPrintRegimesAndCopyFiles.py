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


# TODO: add test for tempering valve
# TODO: cleanup parent ".."
# TODO: add no tempering valve assert to other example


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
        return (
                _pl.Path(_GUI.__file__).parent
                / self.baseFolderRelativePath
                / self.projectName
        )

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
    _PROJECT_NAME,
    _BASE_FOLDER_FILE_PATH,
    _EXPECTED_FILES_PATH,
    _RESULTS_DIR_NAME,
    _RESULTS_DIR_NAME_2,
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

_PROJECT_NAME3 = "diagramWithSourceSinksForRegimes"
pathFinder3 = PathFinder(
    _PROJECT_NAME3,
    _BASE_FOLDER_FILE_PATH,
    _EXPECTED_FILES_PATH,
    _RESULTS_DIR_NAME,
    _RESULTS_DIR_NAME_2,
)
_dataDir = pathFinder3.projectDir
_resultsDir = pathFinder3.resultsDir

_ensureDirExists(_resultsDir)

pathFinder3.setFileEnding("_diagram")
expectedDiagramPath = pathFinder3.expectedPdfPath
newDiagramPath = pathFinder3.newPdfPath

pathFinder3.setFileEnding("_direct")
expectedName1Path = pathFinder3.expectedPdfPath
newName1Path = pathFinder3.newPdfPath

pathFinder3.setFileEnding("_charge")
expectedName2Path = pathFinder3.expectedPdfPath
newName2Path = pathFinder3.newPdfPath

pathFinder3.setFileEnding("_discharge")
expectedName3Path = pathFinder3.expectedPdfPath
newName3Path = pathFinder3.newPdfPath

pathFinder3.setFileEnding("_charge_while_direct")
expectedName4Path = pathFinder3.expectedPdfPath
newName4Path = pathFinder3.newPdfPath


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
        """Checks whether Inkscape is installed correctly."""
        assert "pdf" in _mpltc.comparable_formats()
        assert "svg" in _mpltc.comparable_formats()

    def testUsingQtBot(self, qtbot):
        mainWindow = _createMainWindow(_DATA_DIR, _PROJECT_NAME, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(
            _PROJECT_NAME,
            _DATA_DIR,
            _RESULTS_DIR,
            _REGIMES_FILENAME,
            mainWindow,
        )
        regimeExporter.export()

        filesToCompare = {
            "new_file": [
                _NEW_DIAGRAM_PATH,
                _NEW_NAME1_PATH,
                _NEW_NAME1_SVG_PATH,
                _NEW_NAME2_PATH,
            ],
            "expected_file": [
                _EXPECTED_DIAGRAM_PATH,
                _EXPECTED_NAME1_PATH,
                _EXPECTED_NAME1_SVG_PATH,
                _EXPECTED_NAME2_PATH,
            ],
        }

        errors = []
        for i, newFile in enumerate(filesToCompare["new_file"]):
            try:
                self._fileExistsAndIsCorrect(
                    newFile, filesToCompare["expected_file"][i]
                )
            except AssertionError as currentError:
                errors.append(currentError)

        if errors:
            raise ExceptionGroup("multiple errors", errors)

    @staticmethod
    def _fileExistsAndIsCorrect(producedFile, expectedFile):
        assert producedFile.is_file()
        result = _mpltc.compare_images(
            str(producedFile), str(expectedFile), 0.001, in_decorator=False
        )
        assert result is None

    def testUsingQtBotForGivenRegimes(self, qtbot):
        onlyTheseRegimes = ["name1"]
        mainWindow = _createMainWindow(_DATA_DIR, _PROJECT_NAME, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(
            _PROJECT_NAME,
            _DATA_DIR,
            _RESULTS_DIR_2,
            _REGIMES_FILENAME,
            mainWindow,
        )
        regimeExporter.export(onlyTheseRegimes=onlyTheseRegimes)
        errors = []
        try:
            self._fileExistsAndIsCorrect(
                _NEW_NAME1_PATH_2, _EXPECTED_NAME1_PATH
            )
        except AssertionError as currentError:
            errors.append(currentError)

        try:
            assert not _NEW_DIAGRAM_PATH_2.is_file()
        except AssertionError as currentError:
            errors.append(currentError)

        try:
            assert not _NEW_NAME2_PATH_2.is_file()
        except AssertionError as currentError:
            errors.append(currentError)

        if errors:
            raise ExceptionGroup("multiple errors", errors)

    def testUsingQtBotForRegimeWithTap(self, qtbot):
        onlyTheseRegimes = ["dummy_regime"]
        projectName = "diagramWithTapForRegimes"
        regimeEnding = "_dummy_regime"

        pathFinder2 = PathFinder(
            projectName,
            _BASE_FOLDER_FILE_PATH,
            _EXPECTED_FILES_PATH,
            _RESULTS_DIR_NAME,
            _RESULTS_DIR_NAME_2,
        )
        dataDir = pathFinder2.projectDir
        resultsDir = pathFinder2.resultsDir

        _ensureDirExists(resultsDir)

        pathFinder2.setFileEnding(regimeEnding)

        mainWindow = _createMainWindow(dataDir, projectName, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(
            projectName, dataDir, resultsDir, _REGIMES_FILENAME, mainWindow
        )
        regimeExporter.export(onlyTheseRegimes=onlyTheseRegimes)

        errors = []
        try:
            self._fileExistsAndIsCorrect(
                pathFinder2.newPdfPath, pathFinder2.expectedPdfPath
            )
        except AssertionError as currentError:
            errors.append(currentError)

        pathFinder2.setFileEnding("_diagram")
        try:
            assert not pathFinder2.newPdfPath.is_file()
        except AssertionError as currentError:
            errors.append(currentError)

        if errors:
            raise ExceptionGroup("multiple errors", errors)

    def testUsingQtBotForRegimeWithSourceSinks(self, qtbot):

        mainWindow = _createMainWindow(_dataDir, _PROJECT_NAME3, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(
            _PROJECT_NAME3,
            _dataDir,
            _resultsDir,
            _REGIMES_FILENAME,
            mainWindow,
        )
        regimeExporter.export()

        filesToCompare = {
            "new_file": [
                newDiagramPath,
                newName1Path,
                newName2Path,
                newName3Path,
                newName4Path,
            ],
            "expected_file": [
                expectedDiagramPath,
                expectedName1Path,
                expectedName2Path,
                expectedName3Path,
                expectedName4Path,
            ],
        }

        errors = []
        for i, newFile in enumerate(filesToCompare["new_file"]):
            try:
                self._fileExistsAndIsCorrect(
                    newFile, filesToCompare["expected_file"][i]
                )
            except AssertionError as currentError:
                errors.append(currentError)

        if errors:
            raise ExceptionGroup("multiple errors", errors)

    def testUsingQtBotForDiagramWithTemperingValve(self, qtbot):
        projectName = "diagramWithTemperingValve"

        pathFinder2 = PathFinder(
            projectName,
            _BASE_FOLDER_FILE_PATH,
            _EXPECTED_FILES_PATH,
            _RESULTS_DIR_NAME,
            _RESULTS_DIR_NAME_2,
        )
        dataDir = pathFinder2.projectDir
        resultsDir = pathFinder2.resultsDir

        _ensureDirExists(resultsDir)

        mainWindow = _createMainWindow(dataDir, projectName, qtbot)
        regimeExporter = _rdopfp.RegimeExporter(
            projectName,
            dataDir,
            resultsDir,
            _REGIMES_FILENAME,
            mainWindow,
        )
        regimeExporter.export()

        pathFinder2.setFileEnding("_diagram")
        expectedDiagramPath = pathFinder2.expectedPdfPath
        newDiagramPath = pathFinder2.newPdfPath

        pathFinder2.setFileEnding("_name1")
        expectedName1Path = pathFinder2.expectedPdfPath
        newName1Path = pathFinder2.newPdfPath

        pathFinder2.setFileEnding("_name2")
        expectedName2Path = pathFinder2.expectedPdfPath
        newName2Path = pathFinder2.newPdfPath

        filesToCompare = {
            "new_file": [
                newDiagramPath,
                newName1Path,
                newName2Path,
            ],
            "expected_file": [
                expectedDiagramPath,
                expectedName1Path,
                expectedName2Path,
            ],
        }

        errors = []
        for i, newFile in enumerate(filesToCompare["new_file"]):
            try:
                self._fileExistsAndIsCorrect(
                    newFile, filesToCompare["expected_file"][i]
                )
            except AssertionError as currentError:
                errors.append(currentError)

        # check whether valves are tempering valves again
        try:
            assert 1 == len(regimeExporter.tempering_valves)
            valve = regimeExporter.tempering_valves[0]
            assert valve.isTempering
        except AssertionError as currentError:
            errors.append(currentError)

        if errors:
            raise ExceptionGroup("multiple errors", errors)
