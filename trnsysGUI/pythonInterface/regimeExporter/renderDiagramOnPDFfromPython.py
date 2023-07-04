import dataclasses as _dc
import os as _os
import pathlib as _pl
import subprocess as _sp
import typing as _tp

import PyQt5.QtGui as _qtg
import PyQt5.QtPrintSupport as _qtp
import PyQt5.QtSvg as _qtsvg
import PyQt5.QtCore as _qtc

import trnsysGUI.diagram.Editor as _de
import trnsysGUI.MassFlowVisualizer as _mfv
import trnsysGUI.mainWindow as _mw
import trnsysGUI.pump as _pump
import trnsysGUI.pythonInterface.regimeExporter.getDesiredRegimes as _gdr
import trnsysGUI.TVentil as _tv
import trnsysGUI.WTap_main as _wtm


@_dc.dataclass()
class RegimeExporter:
    projectName: _tp.Union[str, _pl.Path]
    dataDir: _tp.Union[str, _pl.Path]
    resultsDir: _tp.Union[str, _pl.Path]
    regimesFileName: _tp.Union[str, _pl.Path]
    mainWindow: _mw.MainWindow

    def __post_init__(self):
        self.printFilePaths: list = self._getPrtFilePaths()

    def _getPrtFilePaths(self):
        massFlowRatesPrintFileName = f"{self.projectName}_Mfr.prt"
        temperaturesPintFileName = f"{self.projectName}_T.prt"
        massFlowRatesPrintFilePath = self.dataDir / massFlowRatesPrintFileName
        temperaturesPrintFilePath = self.dataDir / temperaturesPintFileName

        return [massFlowRatesPrintFilePath, temperaturesPrintFilePath]

    def export(self, pumpTapPairs=None, onlyTheseRegimes=None):

        if not onlyTheseRegimes:
            self._makeDiagramFiles()

        regimeValues = _gdr.getRegimes(self.dataDir / self.regimesFileName, onlyTheseRegimes)
        pumpsAndValvesNames = list(regimeValues.columns)
        pumpsAndValves, mainTaps = self.getPumpsAndValvesAndMainTaps(pumpsAndValvesNames)

        self._simulateAndVisualizeMassFlows(mainTaps, pumpTapPairs, pumpsAndValves, regimeValues)

    def _makeDiagramFiles(self, regimeName="diagram"):
        pdfName = str(self.resultsDir) + "\\" + self.projectName + "_" + regimeName + ".pdf"
        svgName = str(self.resultsDir) + "\\" + self.projectName + "_" + regimeName + ".svg"
        self._printDiagramToPDF(pdfName)
        self._printDiagramToSVG(svgName)

    def getPumpsAndValvesAndMainTaps(self, pumpsAndValvesNames):
        pumpsAndValves = []
        mainTaps = {}
        blockItemsAndConnections = self.mainWindow.editor.trnsysObj
        for blockItem in blockItemsAndConnections:
            if isinstance(blockItem, (_pump.Pump, _tv.TVentil)):
                if blockItem.displayName in pumpsAndValvesNames:
                    pumpsAndValves.append(blockItem)
            elif isinstance(blockItem, _wtm.WTap_main):
                mainTaps[blockItem.displayName] = blockItem

        return pumpsAndValves, mainTaps

    def _simulateAndVisualizeMassFlows(self, mainTaps, pumpTapPairs, pumpsAndValves, regimeValues):
        massFlowRatesPrintFilePath, temperaturesPrintFilePath = self.printFilePaths

        for regimeName in regimeValues.index:
            regimeRow = regimeValues.loc[regimeName]

            self._adjustPumpsAndValves(pumpsAndValves, regimeRow, pumpTapPairs, mainTaps)

            exception = runMassFlowSolver(self.mainWindow)

            if not exception:
                timeStep = 2
            else:
                regimeName = regimeName + "_FAILED"
                timeStep = 1

            massFlowSolverVisualizer = _mfv.MassFlowVisualizer(
                # type: ignore[attr-defined]  # pylint: disable=unused-variable
                self.mainWindow,
                massFlowRatesPrintFilePath,
                temperaturesPrintFilePath,
            )
            massFlowSolverVisualizer.slider.setValue(timeStep)

            self._makeDiagramFiles(regimeName=regimeName)

            massFlowSolverVisualizer.close()

    @staticmethod
    def _adjustPumpsAndValves(pumpsAndValves, regimeRow, pumpTapPairs, mainTaps):

        for blockItem in pumpsAndValves:
            blockItemName = blockItem.displayName
            desiredValue = regimeRow[blockItemName]
            if isinstance(blockItem, _pump.Pump):
                blockItem.massFlowRateInKgPerH = desiredValue
                if pumpTapPairs and (blockItemName in pumpTapPairs):
                    associatedTap = pumpTapPairs[blockItemName]
                    mainTaps[associatedTap].massFlowRateInKgPerH = desiredValue
            elif isinstance(blockItem, _tv.TVentil):
                blockItem.positionForMassFlowSolver = desiredValue
            else:
                raise TypeError(f"Encountered blockItem of type {blockItem}, instead of a pump or a Valve")

    def _printDiagramToPDF(self, fileName):
        if fileName != "":
            printer = _qtp.QPrinter(_qtp.QPrinter.HighResolution)
            printer.setOrientation(_qtp.QPrinter.Landscape)
            printer.setOutputFormat(_qtp.QPrinter.PdfFormat)
            printer.setOutputFileName(fileName)
            painter = _qtg.QPainter(printer)
            self.mainWindow.editor.diagramScene.render(painter)
            painter.end()

    def _printDiagramToSVG(self, fileName):
        # upside down and tiny compared to canvas
        if fileName != "":
            generator = _qtsvg.QSvgGenerator()
            generator.setSize(_qtc.QSize(1600, 1600))
            generator.setViewBox(_qtc.QRect(0, 0, 1600, 1600))
            generator.setFileName(fileName)
            painter = _qtg.QPainter(generator)
            self.mainWindow.editor.diagramScene.render(painter)
            painter.end()


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


def runDck(cmd, dckName):
    exception = None
    try:
        if _os.path.isfile(dckName):
            _sp.run([cmd, dckName, "/H"], shell=True, check=True)
            skipOthers = False
        else:
            raise FileNotFoundError("File not found: " + dckName)
    except _sp.CalledProcessError as caughtException:
        skipOthers = True
        exception = caughtException

    return skipOthers, exception
