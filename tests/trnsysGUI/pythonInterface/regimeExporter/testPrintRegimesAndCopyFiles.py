import pathlib as _pl

import pytrnsys.utils.log as _ulog

import trnsysGUI as _GUI
import trnsysGUI.mainWindow as _mw
import trnsysGUI.project as _prj
import trnsysGUI.pythonInterface.regimeExporter.renderDiagramOnPDFfromPython as _rdopfp

_PROJECT_NAME_ = "diagramForRegimes"
_DATA_DIR_ = _pl.Path(_GUI.__file__).parent / "..\\tests\\trnsysGUI\\data\\diagramForRegimes"
_DATA_FILENAME_ = "regimes.csv"


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
        assert True is False

# non-qtbot solution?