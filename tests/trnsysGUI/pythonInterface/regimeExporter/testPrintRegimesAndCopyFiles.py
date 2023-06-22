import unittest as _ut
import pathlib as _pl
import diff_pdf_visually as _dpv

import pytrnsys.utils.log as _ulog

import trnsysGUI as _GUI
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj
import trnsysGUI.pythonInterface.regimeExporter.renderDiagramOnPDFfromPython as _rdopfp

_PROJECT_NAME_ = "diagramForRegimes"
_DATA_DIR_ = _pl.Path(_GUI.__file__).parent / "..\\tests\\trnsysGUI\\data\\diagramForRegimes"
_DATA_FILENAME_ = "regimes.csv"
_EXPECTED_PDFS_DIR_ = _DATA_DIR_ / "expectedPDFs"


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
    def testUsingQtBot(self, qtbot):
        mainWindow = _createMainWindow(_DATA_DIR_, _PROJECT_NAME_, qtbot)
        _rdopfp.printRegimesAndCopyFiles(_DATA_DIR_, _PROJECT_NAME_, _DATA_FILENAME_, mainWindow)
        pdfDiagram = _PROJECT_NAME_ + "_diagram.pdf"
        pdfName1 = _PROJECT_NAME_ + "_name1.pdf"
        pdfName2 = _PROJECT_NAME_ + "_name2.pdf"
        pdfPathDiagram = _DATA_DIR_ / pdfDiagram
        pdfPathName1 = _DATA_DIR_ / pdfName1
        pdfPathName2 = _DATA_DIR_ / pdfName2
        assert pdfPathDiagram.is_file()
        assert pdfPathName1.is_file()
        assert pdfPathName2.is_file()
        _dpv.pdf_similar(pdfPathDiagram, _EXPECTED_PDFS_DIR_ / pdfDiagram)
        _dpv.pdf_similar(pdfPathName1, _EXPECTED_PDFS_DIR_ / pdfName1)
        _dpv.pdf_similar(pdfPathName2, _EXPECTED_PDFS_DIR_ / pdfName2)

    def testUsingQtBotForGivenRegimes(self, qtbot):
        onlyTheseRegimes = ["name1"]
        mainWindow = _createMainWindow(_DATA_DIR_, _PROJECT_NAME_, qtbot)
        _rdopfp.printRegimesAndCopyFiles(_DATA_DIR_, _PROJECT_NAME_, _DATA_FILENAME_, mainWindow, onlyTheseRegimes=onlyTheseRegimes)
        pdfDiagram = _PROJECT_NAME_ + "_diagram.pdf"
        pdfName1 = _PROJECT_NAME_ + "_name1.pdf"
        pdfName2 = _PROJECT_NAME_ + "_name2.pdf"
        pdfPathDiagram = _DATA_DIR_ / pdfDiagram
        pdfPathName1 = _DATA_DIR_ / pdfName1
        pdfPathName2 = _DATA_DIR_ / pdfName2
        assert not pdfPathDiagram.is_file()
        assert pdfPathName1.is_file()
        assert not pdfPathName2.is_file()
        _dpv.pdf_similar(pdfPathName1, _EXPECTED_PDFS_DIR_ / pdfName1)





# non-qtbot solution?