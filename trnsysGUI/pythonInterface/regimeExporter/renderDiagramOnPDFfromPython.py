import os as _os
import pathlib as _pl
import pytest as _pt
import subprocess as _sp
import typing as _tp

import PyQt5.QtGui as _qtg
import PyQt5.QtPrintSupport as _qtp

from tests.trnsysGUI.diagram import _testHelper as _th
import trnsysGUI.project as _prj
import trnsysGUI as _GUI
import trnsysGUI.pythonInterface.regimeExporter.getDesiredRegimes as _gdr
import trnsysGUI.mainWindow as _mw
import trnsysGUI.MassFlowVisualizer as _mfv
import trnsysGUI.diagram.Editor as _de


# regimeValue = {regimeName: "", pumps: [], valves [] }
# regimeValues = df[]
# for regimeRow in df:
import trnsysGUI.pump as _pump
import trnsysGUI.TVentil as _tv


def getPumpsAndValves(pumpsAndValvesNames, mainWindow):
    pumpsAndValves = []
    blockItemsAndConnections = mainWindow.editor.trnsysObj
    for blockItem in blockItemsAndConnections:
        if isinstance(blockItem, _pump.Pump) or isinstance(blockItem, _tv.TVentil):
            if blockItem.displayName in pumpsAndValvesNames:
                pumpsAndValves.append(blockItem)
    return pumpsAndValves


def printRegimesAndCopyFiles(_DATA_DIR_, _PROJECT_NAME_, _DATA_FILENAME_, mainWindow):
    # createPDF of diagram only

    regimeValues = _gdr.getRegimesFromFile(_DATA_DIR_ / _DATA_FILENAME_)
    pumpsAndValvesNames = list(regimeValues.columns)
    pumpsAndValvesNames.remove('regimeName')
    massFlowRatesPrintFileName = f"{_PROJECT_NAME_}_Mfr.prt"
    temperaturesPintFileName = f"{_PROJECT_NAME_}_T.prt"
    massFlowRatesPrintFilePath = _DATA_DIR_ / massFlowRatesPrintFileName
    temperaturesPrintFilePath = _DATA_DIR_ / temperaturesPintFileName
    pumpsAndValves = getPumpsAndValves(pumpsAndValvesNames, mainWindow)

    for ix in regimeValues.index:
        regimeRow = regimeValues.loc[ix]
        regimeName = regimeRow["regimeName"]

        adjustPumpsAndValves(pumpsAndValves, regimeRow)

        exception = runMassFlowSolver(mainWindow)

        if not exception:
            print("massflowSolver ran without issue")
            # copyMFRandTfiles()
            timeStep = 2
        else:
            regimeName = regimeName + "_FAILED"
            timeStep = 1

        massFlowSolverVisualizer = _mfv.MassFlowVisualizer(  # type: ignore[attr-defined]  # pylint: disable=unused-variable
            mainWindow, massFlowRatesPrintFilePath, temperaturesPrintFilePath
        )
        massFlowSolverVisualizer.slider.setValue(timeStep)

        pdfName = str(_DATA_DIR_) + "\\" + _PROJECT_NAME_ + "_" + regimeName + ".pdf"
        print(pdfName)
        printDiagramToPDF(pdfName, mainWindow)
        break


def adjustPumpsAndValves(pumpsAndValves, regimeRow):

    for blockItem in pumpsAndValves:
        blockItemName = blockItem.displayName
        desiredValue = regimeRow[blockItemName]
        if isinstance(blockItem, _pump.Pump):
            # assert desiredValue meaningful
            blockItem.massFlowRateInKgPerH = desiredValue
        elif isinstance(blockItem, _tv.TVentil):
            # assert desiredValue meaningful
            blockItem.positionForMassFlowSolver = desiredValue
        else:
            raise TypeError(f'Encountered blockItem of type {blockItem}, instead of a pump or a Valve')


def runMassFlowSolver(mainWindow) -> _tp.Optional[Exception]:
    exception = _exportMassFlowSolverDeckAndRunTrnsys(mainWindow.editor)
    return exception


def _exportMassFlowSolverDeckAndRunTrnsys(editor: _de.Editor):  # type: ignore[name-defined]
    exportedFilePath = str(_exportHydraulic(editor, _format="mfs"))

    trnExePath = str(_getTrnExePath())

    skipOther, exception = runDck(trnExePath, exportedFilePath)
    return exception


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


def runDck(cmd, dckName):
    exception = None
    try:
        if _os.path.isfile(dckName):
            _sp.run([cmd, dckName, "/H"], shell=True, check=True)
            skipOthers = False
        else:
            raise FileNotFoundError("File not found: " + dckName)
    except Exception as e:
        skipOthers = True
        exception = e

    return skipOthers, exception
