import os as _os
import pathlib as _pl
import subprocess as _sp
import typing as _tp

import PyQt5.QtGui as _qtg
import PyQt5.QtPrintSupport as _qtp
import PyQt5.QtSvg as _qtsvg
import PyQt5.QtCore as _qtc

import trnsysGUI.pythonInterface.regimeExporter.getDesiredRegimes as _gdr
import trnsysGUI.MassFlowVisualizer as _mfv
import trnsysGUI.diagram.Editor as _de


import trnsysGUI.pump as _pump
import trnsysGUI.TVentil as _tv

import trnsysGUI.WTap_main as _wtm


def getPumpsAndValvesAndMainTaps(pumpsAndValvesNames, mainWindow):
    pumpsAndValves = []
    mainTaps = {}
    blockItemsAndConnections = mainWindow.editor.trnsysObj
    for blockItem in blockItemsAndConnections:
        if isinstance(blockItem, (_pump.Pump, _tv.TVentil)):
            if blockItem.displayName in pumpsAndValvesNames:
                pumpsAndValves.append(blockItem)
        elif isinstance(blockItem, _wtm.WTap_main):
            mainTaps[blockItem.displayName] = blockItem

    return pumpsAndValves, mainTaps


def printRegimesAndCopyFiles(
    dataDir, projectName, resultsDir, dataFileName, mainWindow, pumpTapPairs=None, onlyTheseRegimes=None
):
    # createPDF of diagram only
    if not onlyTheseRegimes:
        makeDiagramFiles(projectName, resultsDir, mainWindow)

    regimeValues = _gdr.getRegimes(dataDir / dataFileName, onlyTheseRegimes)
    pumpsAndValvesNames = list(regimeValues.columns)
    pumpsAndValves, mainTaps = getPumpsAndValvesAndMainTaps(pumpsAndValvesNames, mainWindow)
    massFlowRatesPrintFilePath, temperaturesPrintFilePath = getPrtFilePaths(dataDir, projectName)

    for regimeName in regimeValues.index:
        regimeRow = regimeValues.loc[regimeName]

        adjustPumpsAndValves(pumpsAndValves, regimeRow, pumpTapPairs, mainTaps)

        exception = runMassFlowSolver(mainWindow)

        if not exception:
            timeStep = 2
        else:
            regimeName = regimeName + "_FAILED"
            timeStep = 1

        massFlowSolverVisualizer = _mfv.MassFlowVisualizer(  # type: ignore[attr-defined]  # pylint: disable=unused-variable
            mainWindow, massFlowRatesPrintFilePath, temperaturesPrintFilePath
        )
        massFlowSolverVisualizer.slider.setValue(timeStep)

        makeDiagramFiles(projectName, resultsDir, mainWindow, regimeName=regimeName)

        massFlowSolverVisualizer.close()


def getPrtFilePaths(dataDir, projectName):
    massFlowRatesPrintFileName = f"{projectName}_Mfr.prt"
    temperaturesPintFileName = f"{projectName}_T.prt"
    massFlowRatesPrintFilePath = dataDir / massFlowRatesPrintFileName
    temperaturesPrintFilePath = dataDir / temperaturesPintFileName
    return massFlowRatesPrintFilePath, temperaturesPrintFilePath


def makeDiagramFiles(projectName, resultsDir, mainWindow, regimeName="diagram"):
    pdfName = str(resultsDir) + "\\" + projectName + "_" + regimeName + ".pdf"
    svgName = str(resultsDir) + "\\" + projectName + "_" + regimeName + ".svg"
    printDiagramToPDF(pdfName, mainWindow)
    printDiagramToSVG(svgName, mainWindow)


def adjustPumpsAndValves(pumpsAndValves, regimeRow, pumpTapPairs, mainTaps):

    for blockItem in pumpsAndValves:
        blockItemName = blockItem.displayName
        desiredValue = regimeRow[blockItemName]
        if isinstance(blockItem, _pump.Pump):
            # assert desiredValue meaningful
            blockItem.massFlowRateInKgPerH = desiredValue
            if pumpTapPairs and (blockItemName in pumpTapPairs):
                associatedTap = pumpTapPairs[blockItemName]
                mainTaps[associatedTap].massFlowRateInKgPerH = desiredValue
        elif isinstance(blockItem, _tv.TVentil):
            # assert desiredValue meaningful
            blockItem.positionForMassFlowSolver = desiredValue
        else:
            raise TypeError(f"Encountered blockItem of type {blockItem}, instead of a pump or a Valve")


def runMassFlowSolver(mainWindow) -> _tp.Optional[Exception]:
    exception = _exportMassFlowSolverDeckAndRunTrnsys(mainWindow.editor)
    return exception


def _exportMassFlowSolverDeckAndRunTrnsys(editor: _de.Editor):  # type: ignore[name-defined]
    exportedFilePath = str(_exportHydraulic(editor, formatting="mfs"))

    trnExePath = str(_getTrnExePath())

    _, exception = runDck(trnExePath, exportedFilePath)
    return exception


def _exportHydraulic(editor: _de.Editor, *, formatting) -> str:  # type: ignore[name-defined]
    exportedFilePath = editor.exportHydraulics(exportTo=formatting)
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


def printDiagramToSVG(fileName, mainWindow):
    # upside down and tiny compared to canvas
    if fileName != "":
        generator = _qtsvg.QSvgGenerator()
        generator.setSize(_qtc.QSize(1600, 1600))
        generator.setViewBox(_qtc.QRect(0, 0, 1600, 1600))
        generator.setFileName(fileName)
        painter = _qtg.QPainter(generator)
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
