import os as _os
import pathlib as _pl
import pytest as _pt
import subprocess as _sp

import PyQt5.QtGui as _qtg
import PyQt5.QtPrintSupport as _qtp

from tests.trnsysGUI.diagram import _testHelper as _th
import trnsysGUI.project as _prj
import trnsysGUI as _GUI
import trnsysGUI.pythonInterface.regimeExporter.getDesiredRegimes as _gdr
import trnsysGUI.mainWindow as _mw
import trnsysGUI.diagram.Editor as _de


# regimeValue = {regimeName: "", pumps: [], valves [] }
# regimeValues = df[]
# for regimeRow in df:


def printRegimesAndCopyFiles(_DATA_DIR_, _PROJECT_NAME_, _DATA_FILENAME_, mainWindow):
    regimeValues = _gdr.getRegimesFromFile(_DATA_DIR_ / _DATA_FILENAME_)
    for ix in regimeValues.index:
        regimeRow = regimeValues.loc[ix]
        regimeName = regimeRow["regimeName"]
        print(regimeName)
        # adjustPumpsAndValves()
        runMassFlowSolver(mainWindow)
        # copyMFRandTfiles()
        # adjustSlider(steps=2)

        pdfName = str(_DATA_DIR_) + "\\" + _PROJECT_NAME_ + "_" + regimeName + ".pdf"
        print(pdfName)
        printDiagramToPDF(pdfName, mainWindow)
        break


def runMassFlowSolver(mainWindow) -> None:
    try:
        _exportMassFlowSolverDeckAndRunTrnsys(mainWindow.editor)
    except Exception:
        raise

    # massFlowSolverDeckFileName = f"{PROJECT_NAME}_mfs.dck"

    # copyMFRandTfiles(NAME, regimeName)
    #     massFlowRatesPrintFileName = f"{PROJECT_NAME}_Mfr.prt"
    #     temperaturesPintFileName = f"{PROJECT_NAME}_T.prt"

    # moveSlider(steps=2)
    # printDiagramToPDF()


def _exportMassFlowSolverDeckAndRunTrnsys(editor: _de.Editor):  # type: ignore[name-defined]
    exportedFilePath = _exportHydraulic(editor, _format="mfs")

    trnExePath = _getTrnExePath()

    _sp.run([str(trnExePath), str(exportedFilePath), "/H"], check=True)


def _exportHydraulic(editor: _de.Editor, *, _format) -> str:  # type: ignore[name-defined]
    exportedFilePath = editor.exportHydraulics(exportTo=_format)
    return exportedFilePath


def _getTrnExePath():
    isRunDuringCi = _os.environ.get("CI") == "true"
    if isRunDuringCi:
        return _pl.PureWindowsPath(r"C:\CI-Progams\TRNSYS18\Exe\TrnEXE.exe")

    return _pl.PureWindowsPath(r"C:\TRNSYS18\Exe\TrnEXE.exe")


def printDiagramToPDF(fileName, mainWindow):
    if fileName != "":
        printer = _qtp.QPrinter(_qtp.QPrinter.HighResolution)
        printer.setOrientation(_qtp.QPrinter.Landscape)
        printer.setOutputFormat(_qtp.QPrinter.PdfFormat)
        printer.setOutputFileName(fileName)
        painter = _qtg.QPainter(printer)
        mainWindow.editor.diagramScene.render(painter)
        painter.end()
