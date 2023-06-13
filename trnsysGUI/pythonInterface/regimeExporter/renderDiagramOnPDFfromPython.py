import PyQt5.QtGui as _qtg
import PyQt5.QtPrintSupport as _qtp

from tests.trnsysGUI.diagram import _testHelper as _th
import trnsysGUI.project as _prj


def printDiagramToPDF(self, fileName):
    if fileName != "":
        printer = _qtp.QPrinter(_qtp.QPrinter.HighResolution)
        printer.setOrientation(_qtp.QPrinter.Landscape)
        printer.setOutputFormat(_qtp.QPrinter.PdfFormat)
        printer.setOutputFileName(fileName)
        painter = _qtg.QPainter(printer)
        self.diagramScene.render(painter)
        painter.end()
        self.logger.info("File exported to %s" % fileName)

# regimeValue = {regimeName: "", pumps: [], valves [] }
# regimeValues = df[]
# for regimeRow in df:



PROJECT_NAME = "PCM_reverseable_airsource_HP_reduced"
PROJECT_FOLDER = "."

def printRegimesAndCopyFiles():
    mainWindow = self._createMainWindow(PROJECT_FOLDER, PROJECT_NAME, qtbot, monkeypatch)

    regimeValues = getRegimesValues()
    for regimeRow in regimeValues.rows():
        adjustPumpsAndValves()
        runMassFlowSolver()
        copyMFRandTfiles()
        adjustSlider(steps=2)
        printDiagramToPDF()



def runMassFlowSolver(self, PROJECT_NAME, PROJECT_FOLDER, qtbot, monkeypatch) -> None:

    self._exportMassFlowSolverDeckAndRunTrnsys(mainWindow.editor)

    # massFlowSolverDeckFileName = f"{PROJECT_NAME}_mfs.dck"

    # copyMFRandTfiles(NAME, regimeName)
    #     massFlowRatesPrintFileName = f"{PROJECT_NAME}_Mfr.prt"
    #     temperaturesPintFileName = f"{PROJECT_NAME}_T.prt"

    # moveSlider(steps=2)
    # printDiagramToPDF()


def _createMainWindow(PROJECT_FOLDER, PROJECT_NAME, qtbot, monkeypatch):
    def patchedCloseEvent(_, closeEvent):
            return closeEvent.accept()

    monkeypatch.setattr(
        _mw.MainWindow,  # type: ignore[attr-defined]
        _mw.MainWindow.closeEvent.__name__,  # type: ignore[attr-defined]
        patchedCloseEvent,
    )

    projectJsonFilePath = PROJECT_FOLDER / f"{PROJECT_NAME}.json"
    project = _prj.LoadProject(projectJsonFilePath)

    logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]

    mainWindow = _mw.MainWindow(logger, project)  # type: ignore[attr-defined]

    qtbot.addWidget(mainWindow)

    return mainWindow
