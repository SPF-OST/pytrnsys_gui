import pathlib as _pl

import PyQt5.QtWidgets as _qtw

import trnsysGUI.mainWindow as mw
import trnsysGUI.pythonInterface.regimeExporter.renderDiagramOnPDFfromPython as rdopfp
from trnsysGUI import constants
from trnsysGUI import project as prj
from trnsysGUI.messageBox import MessageBox
from trnsysGUI.pythonInterface.regimeExporter import exportRegimes as er


def createModesTemplate(project: prj.Project):
    modesTemplateFile = f"{project.jsonFilePath.parent}/{constants.MODES_TEMPLATE_FILE_NAME}"  # type: ignore[union-attr]
    if _pl.Path(modesTemplateFile).exists():
        if MessageBox.create(messageText=constants.MODE_CSV_ALREADY_EXISTS) == _qtw.QMessageBox.Cancel:
            return
    er.exportRegimeTemplate(project.jsonFilePath, modesTemplateFile)  # type: ignore[union-attr]
    MessageBox.create(messageText=constants.MODE_CSV_CRATED, buttons=[_qtw.QMessageBox.Ok])


def runModes(project: prj.Project, mainWindow: mw.MainWindow):  # type: ignore[name-defined]
    try:
        projectDir = project.jsonFilePath.parent  # type: ignore[union-attr]
        projectName = project.jsonFilePath.stem  # type: ignore[union-attr]
        resultsDir = _pl.Path(f"{projectDir}/diagrams")
        resultsDir.mkdir(exist_ok=True)

        re = rdopfp.RegimeExporter(projectName, projectDir, resultsDir, constants.MODES_TEMPLATE_FILE_NAME, mainWindow)
        re.export()

    except FileNotFoundError as e:
        MessageBox.create(
            messageText=constants.ERROR_RUNNING_MODES, informativeText=str(e.filename), buttons=[_qtw.QMessageBox.Ok]
        )
