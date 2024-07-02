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
import trnsysGUI.pumpsAndTaps.pump as _pump
import trnsysGUI.pythonInterface.regimeExporter.getDesiredRegimes as _gdr
import trnsysGUI.TVentil as _tv
import trnsysGUI.pumpsAndTaps._tapBase as _tb


@_dc.dataclass
class RegimeExporter:
    projectName: str
    projectDir: _pl.Path
    resultsDir: _pl.Path
    regimesFileName: str
    mainWindow: _mw.MainWindow  # type: ignore[name-defined]

    @property
    def massFlowRatesPrintFilePath(self):
        massFlowRatesPrintFileName = f"{self.projectName}_Mfr.prt"
        return self.projectDir / massFlowRatesPrintFileName

    @property
    def temperaturesPrintFilePath(self):
        temperaturesPintFileName = f"{self.projectName}_T.prt"
        return self.projectDir / temperaturesPintFileName

    def export(
        self, onlyTheseRegimes: _tp.Optional[_tp.Sequence[str]] = None
    ) -> None:

        if not onlyTheseRegimes:
            self._makeDiagramFiles()

        regimeValues = _gdr.getRegimes(self.projectDir / self.regimesFileName, onlyTheseRegimes)
        pumpsAndValvesAndTapsNames = list(regimeValues.columns)
        pumpsAndValvesAndTaps = self.getPumpsAndValvesAndMainTaps(pumpsAndValvesAndTapsNames)

        self._simulateAndVisualizeMassFlows(pumpsAndValvesAndTaps, regimeValues)

    def _makeDiagramFiles(self, regimeName="diagram") -> None:
        pdfName = self.resultsDir / f"{self.projectName}_{regimeName}.pdf"
        svgName = self.resultsDir / f"{self.projectName}_{regimeName}.svg"
        self._printDiagramToPDF(pdfName)
        self._printDiagramToSVG(svgName)

    def getPumpsAndValvesAndMainTaps(self, pumpsAndValvesNames):
        pumpsAndValvesAndTaps = []
        blockItemsAndConnections = self.mainWindow.editor.trnsysObj
        for blockItem in blockItemsAndConnections:
            if isinstance(blockItem, (_pump.Pump, _tv.TVentil, _tb.TapBase)):
                if blockItem.displayName in pumpsAndValvesNames:
                    pumpsAndValvesAndTaps.append(blockItem)

        return pumpsAndValvesAndTaps

    def _simulateAndVisualizeMassFlows(self, pumpsAndValvesAndTaps, regimeValues) -> None:

        for regimeName in regimeValues.index:
            regimeRow = regimeValues.loc[regimeName]

            self._adjustPumpsAndValves(pumpsAndValvesAndTaps, regimeRow)

            exception = runMassFlowSolver(self.mainWindow)

            if not exception:
                timeStep = 2
            else:
                regimeName = regimeName + "_FAILED"
                timeStep = 1

            massFlowSolverVisualizer = _mfv.MassFlowVisualizer(  # type: ignore[attr-defined]
                self.mainWindow,
                self.massFlowRatesPrintFilePath,
                self.temperaturesPrintFilePath,
            )
            massFlowSolverVisualizer.slider.setValue(timeStep)

            self._makeDiagramFiles(regimeName=regimeName)

            massFlowSolverVisualizer.close()

    @staticmethod
    def _adjustPumpsAndValves(pumpsAndValvesAndTaps, regimeRow) -> None:

        for blockItem in pumpsAndValvesAndTaps:
            blockItemName = blockItem.displayName
            desiredValue = regimeRow[blockItemName]

            if isinstance(blockItem, (_pump.Pump, _tb.TapBase)):
                blockItem.massFlowRateInKgPerH = desiredValue

            elif isinstance(blockItem, _tv.TVentil):
                blockItem.positionForMassFlowSolver = desiredValue

            else:
                raise AssertionError(f"Encountered blockItem of type {blockItem}, instead of a pump or a Valve")

    def _printDiagramToPDF(self, fileName: _pl.Path) -> None:
        if fileName != "":
            printer = _qtp.QPrinter(_qtp.QPrinter.HighResolution)
            printer.setOrientation(_qtp.QPrinter.Landscape)
            printer.setOutputFormat(_qtp.QPrinter.PdfFormat)
            printer.setOutputFileName(str(fileName))
            painter = _qtg.QPainter(printer)
            self.mainWindow.editor.diagramScene.render(painter)
            painter.end()

    def _printDiagramToSVG(self, fileName: _pl.Path) -> None:
        # upside down and tiny compared to canvas
        if fileName != "":
            generator = _qtsvg.QSvgGenerator()
            generator.setSize(_qtc.QSize(1600, 1600))
            generator.setViewBox(_qtc.QRect(0, 0, 1600, 1600))
            generator.setFileName(str(fileName))
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
