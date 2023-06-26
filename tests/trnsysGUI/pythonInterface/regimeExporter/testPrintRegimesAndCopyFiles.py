import pathlib as _pl
import matplotlib.testing.compare as _mpltc

import pytrnsys.utils.log as _ulog

import trnsysGUI as _GUI
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj
import trnsysGUI.pythonInterface.regimeExporter.renderDiagramOnPDFfromPython as _rdopfp

_PROJECT_NAME_ = "diagramForRegimes"
_DATA_DIR_ = _pl.Path(_GUI.__file__).parent / f"..\\tests\\trnsysGUI\\data\\{_PROJECT_NAME_}"
_DATA_FILENAME_ = "regimes.csv"
_EXPECTED_PDFS_DIR_ = _DATA_DIR_ / "expectedPDFs"

_DIAGRAM_ENDING_ = "_diagram.pdf"
_NAME1_ENDING_ = "_name1.pdf"
_NAME2_ENDING_ = "_name2.pdf"
_NAME1_SVG_ENDING_ = "_name1.svg"


def _getExpectedAndNewFilePaths(ending):
    pdfName = _PROJECT_NAME_ + ending
    expectedPdfPath = _EXPECTED_PDFS_DIR_ / pdfName
    newPdfPath = _DATA_DIR_ / pdfName
    return expectedPdfPath, newPdfPath


_EXPECTED_DIAGRAM_PATH_, _NEW_DIAGRAM_PATH_ = _getExpectedAndNewFilePaths(_DIAGRAM_ENDING_)
_EXPECTED_NAME1_PATH_, _NEW_NAME1_PATH_ = _getExpectedAndNewFilePaths(_NAME1_ENDING_)
_EXPECTED_NAME2_PATH_, _NEW_NAME2_PATH_ = _getExpectedAndNewFilePaths(_NAME2_ENDING_)
_EXPECTED_NAME1_SVG_PATH_, _NEW_NAME1_SVG_PATH_ = _getExpectedAndNewFilePaths(_NAME1_SVG_ENDING_)


def _createMainWindow(PROJECT_FOLDER, PROJECT_NAME, qtbot):
    projectJsonFilePath = PROJECT_FOLDER / f"{PROJECT_NAME}.json"
    project = _prj.LoadProject(projectJsonFilePath)

    logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

    mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

    qtbot.addWidget(mainWindow)
    mainWindow.showBoxOnClose = False
    mainWindow.editor.forceOverwrite = True

    return mainWindow


class TestPrintRegimesAndCopyFiles:
    def testMplInstallation(self):
        assert 'pdf' in _mpltc.comparable_formats()
        assert 'svg' in _mpltc.comparable_formats()

    def testUsingQtBot(self, qtbot):
        mainWindow = _createMainWindow(_DATA_DIR_, _PROJECT_NAME_, qtbot)
        _rdopfp.printRegimesAndCopyFiles(_DATA_DIR_, _PROJECT_NAME_, _DATA_FILENAME_, mainWindow)

        self._FileExistsAndIsCorrect(_NEW_DIAGRAM_PATH_, _EXPECTED_DIAGRAM_PATH_)
        self._FileExistsAndIsCorrect(_NEW_NAME1_PATH_, _EXPECTED_NAME1_PATH_)
        self._FileExistsAndIsCorrect(_NEW_NAME1_SVG_PATH_, _EXPECTED_NAME1_SVG_PATH_)
        self._FileExistsAndIsCorrect(_NEW_NAME2_PATH_, _EXPECTED_NAME2_PATH_)


    @staticmethod
    def _FileExistsAndIsCorrect(producedFile, expectedFile):
        assert producedFile.is_file()
        _mpltc.compare_images(str(producedFile), str(expectedFile), 0, in_decorator=False)

    def testUsingQtBotForGivenRegimes(self, qtbot):
        onlyTheseRegimes = ["name1"]
        mainWindow = _createMainWindow(_DATA_DIR_, _PROJECT_NAME_, qtbot)
        _rdopfp.printRegimesAndCopyFiles(
            _DATA_DIR_, _PROJECT_NAME_, _DATA_FILENAME_, mainWindow, onlyTheseRegimes=onlyTheseRegimes
        )
        self._FileExistsAndIsCorrect(_NEW_NAME1_PATH_, _EXPECTED_NAME1_PATH_)
        self._FileExistsAndIsCorrect(_NEW_NAME1_PATH_, _EXPECTED_DIAGRAM_PATH_)
        assert not _NEW_DIAGRAM_PATH_.is_file()
        assert not _NEW_NAME2_PATH_.is_file()


# non-qtbot solution?
