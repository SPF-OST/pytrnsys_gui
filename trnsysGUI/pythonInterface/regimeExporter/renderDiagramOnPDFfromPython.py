from __future__ import annotations

import collections.abc as _cabc
import dataclasses as _dc
import os as _os
import pathlib as _pl
import subprocess as _sp
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtPrintSupport as _qtp
import PyQt5.QtSvg as _qtsvg
import pandas as _pd

import trnsysGUI.MassFlowVisualizer as _mfv
import trnsysGUI.TVentil as _tv
import trnsysGUI.diagram.Editor as _de
import trnsysGUI.pumpsAndTaps._tapBase as _tb
import trnsysGUI.pumpsAndTaps.pump as _pump
import trnsysGUI.pythonInterface.regimeExporter.getDesiredRegimes as _gdr
import trnsysGUI.sourceSinkBase as _ssb

if _tp.TYPE_CHECKING:
    import trnsysGUI.mainWindow as _mw


_BlockItems = (_pump.Pump, _tv.TVentil, _tb.TapBase, _ssb.SourceSinkBase)
_BlockItem = _pump.Pump | _tv.TVentil | _tb.TapBase | _ssb.SourceSinkBase


@_dc.dataclass
class RegimeExporter:
    projectName: str
    projectDir: _pl.Path
    resultsDir: _pl.Path
    regimesFileName: str
    mainWindow: _mw.MainWindow  # type: ignore[name-defined]
    temperingValveWasTrue: bool = False

    def __post_init__(self) -> None:
        self._temperingValves: list[_tv.TVentil] = []

    @property
    def massFlowRatesPrintFilePath(self) -> _pl.Path:
        massFlowRatesPrintFileName = f"{self.projectName}_Mfr.prt"
        return self.projectDir / massFlowRatesPrintFileName

    @property
    def temperaturesPrintFilePath(self) -> _pl.Path:
        temperaturesPintFileName = f"{self.projectName}_T.prt"
        return self.projectDir / temperaturesPintFileName

    @property
    def temperingValves(self) -> _cabc.Sequence[_tv.TVentil]:
        return self._temperingValves

    def export(
        self, onlyTheseRegimes: _tp.Optional[_tp.Sequence[str]] = None
    ) -> _tp.List[str]:

        if not onlyTheseRegimes:
            self._makeDiagramFiles()

        regimeValues = _gdr.getRegimes(
            self.projectDir / self.regimesFileName, onlyTheseRegimes
        )
        relevantNames = list(regimeValues.columns)
        relevantBlockItems = self.getRelevantBlockItems(relevantNames)

        return self._simulateAndVisualizeMassFlows(
            relevantBlockItems, regimeValues
        )

    def _makeDiagramFiles(self, regimeName: str = "diagram") -> None:
        pdfName = self.resultsDir / f"{self.projectName}_{regimeName}.pdf"
        svgName = self.resultsDir / f"{self.projectName}_{regimeName}.svg"
        self._printDiagramToPDF(pdfName)
        self._printDiagramToSVG(svgName)

    def getRelevantBlockItems(
        self, relevantNames: _tp.Sequence[str]
    ) -> _tp.Sequence[_BlockItem]:
        blockItemsAndConnections = self.mainWindow.editor.trnsysObj

        pumpsAndValvesAndTaps = [
            b
            for b in blockItemsAndConnections
            if isinstance(b, _BlockItems) and b.displayName in relevantNames
        ]

        return pumpsAndValvesAndTaps

    def _simulateAndVisualizeMassFlows(
        self,
        relevantBlockItems: _tp.Sequence[_BlockItem],
        regimeValues: _pd.DataFrame,
    ) -> _tp.List[str]:
        failures = []
        for regimeName in regimeValues.index:
            regimeRow = regimeValues.loc[regimeName]

            self._adjustPumpsAndValves(relevantBlockItems, regimeRow)

            try:
                _exportMassFlowSolverDeckAndRunTrnsys(self.mainWindow.editor)
                timeStep = 2
            except (FileNotFoundError, _sp.CalledProcessError):
                failures.append(regimeName)
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

        self._resetTemperingValves()
        return failures

    def _adjustPumpsAndValves(
        self,
        relevantBlockItems: _tp.Sequence[_BlockItem],
        regimeRow: _pd.Series,
    ) -> None:
        for blockItem in relevantBlockItems:
            blockItemName = blockItem.displayName
            desiredValue = regimeRow[blockItemName]

            match blockItem:
                case (
                    _pump.Pump()
                    | _tb.TapBase()
                    | _ssb.SourceSinkBase() as hasMassFlowRate
                ):
                    hasMassFlowRate.massFlowRateInKgPerH = desiredValue
                case _tv.TVentil() as valve:
                    valve.positionForMassFlowSolver = desiredValue
                    if valve.isTempering:
                        self.temperingValveWasTrue = True
                        valve.isTempering = False
                        self._temperingValves.append(valve)
                case _:
                    _tp.assert_never(blockItem)

    def _printDiagramToPDF(self, fileName: _pl.Path) -> None:
        printer = _qtp.QPrinter(_qtp.QPrinter.HighResolution)
        printer.setOrientation(_qtp.QPrinter.Landscape)
        printer.setOutputFormat(_qtp.QPrinter.PdfFormat)
        printer.setOutputFileName(str(fileName))
        painter = _qtg.QPainter(printer)
        self.mainWindow.editor.diagramScene.render(painter)
        painter.end()

    def _printDiagramToSVG(self, fileName: _pl.Path) -> None:
        # upside down and tiny compared to canvas
        generator = _qtsvg.QSvgGenerator()
        generator.setSize(_qtc.QSize(1600, 1600))
        generator.setViewBox(_qtc.QRect(0, 0, 1600, 1600))
        generator.setFileName(str(fileName))
        painter = _qtg.QPainter(generator)
        self.mainWindow.editor.diagramScene.render(painter)
        painter.end()

    def _resetTemperingValves(self) -> None:
        if not self.temperingValves:
            return

        for valve in self.temperingValves:
            valve.isTempering = True

        self.temperingValveWasTrue = False


def _exportMassFlowSolverDeckAndRunTrnsys(editor: _de.Editor) -> None:  # type: ignore[name-defined]
    exportedFilePath = str(_exportHydraulic(editor, formatting="mfs"))

    trnExePath = str(_getTrnExePath())

    runDck(trnExePath, exportedFilePath)


def _exportHydraulic(editor: _de.Editor, *, formatting) -> str:  # type: ignore[name-defined]
    exportedFilePath = editor.exportHydraulics(
        exportTo=formatting, disableFileExistMsgb=True
    )
    return exportedFilePath


def _getTrnExePath() -> _pl.PureWindowsPath:
    isRunDuringCi = _os.environ.get("CI") == "true"
    if isRunDuringCi:
        return _pl.PureWindowsPath(r"C:\CI-Progams\TRNSYS18_pytrnsys\Exe\TrnEXE.exe")

    return _pl.PureWindowsPath(
        r"C:\TRNSYS18\Exe\TrnEXE.exe"
    )  # pragma: no cover


def runDck(cmd: str, dckName: str) -> None:
    if not _os.path.isfile(dckName):
        raise FileNotFoundError(
            "File not found: " + dckName
        )  # pragma: no cover

    _sp.run([cmd, dckName, "/H"], shell=True, check=True)
