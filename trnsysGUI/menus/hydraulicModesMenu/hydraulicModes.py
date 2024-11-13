from __future__ import annotations

import pathlib as _pl
import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.pythonInterface.regimeExporter.renderDiagramOnPDFfromPython as rdopfp
from trnsysGUI import constants
from trnsysGUI import project as prj
from trnsysGUI.messageBox import MessageBox
from trnsysGUI.pythonInterface.regimeExporter import exportRegimes as er

if _tp.TYPE_CHECKING:  # pragma: no cover
    import trnsysGUI.mainWindow as mw


def createModesTemplate(project: prj.CreateOrLoadProject):
    modesTemplateFile = (
        f"{project.jsonFilePath.parent}/{constants.MODES_TEMPLATE_FILE_NAME}"
    )
    if (
        _pl.Path(modesTemplateFile).exists()
        and MessageBox.create(messageText=constants.MODE_CSV_ALREADY_EXISTS)
        == _qtw.QMessageBox.Cancel
    ):
        return
    er.exportRegimeTemplate(project.jsonFilePath, modesTemplateFile)
    MessageBox.create(
        messageText=constants.MODES_CSV_CREATED,
        informativeText=constants.MODES_CSV_CREATED_ADDITIONAL,
        buttons=[_qtw.QMessageBox.Ok],
    )


def runModes(project: prj.CreateOrLoadProject, mainWindow: mw.MainWindow):  # type: ignore[name-defined]
    try:
        projectDir = project.jsonFilePath.parent
        projectName = project.jsonFilePath.stem
        resultsDir = _pl.Path(f"{projectDir}/diagrams")
        resultsDir.mkdir(exist_ok=True)
        modesFile, _ = _qtw.QFileDialog.getOpenFileName(
            caption="Select modes csv to run",
            filter="*.csv",
            directory=str(projectDir),
        )
        if not modesFile:
            return
        re = rdopfp.RegimeExporter(
            projectName, projectDir, resultsDir, modesFile, mainWindow
        )
        failures = re.export()

        if failures:
            MessageBox.create(
                messageText=f"{constants.ERROR_RUNNING_MODES}{','.join(failures)}",
                informativeText=constants.ERROR_RUNNING_MODES_TRNSYS_ADDITIONAL,
                buttons=[_qtw.QMessageBox.Ok],
            )
        else:
            MessageBox.create(
                messageText=f"{constants.SUCCESS_RUNNING_MODES}{','.join(failures)}",
                buttons=[_qtw.QMessageBox.Ok],
            )

    except FileNotFoundError as e:
        MessageBox.create(
            messageText=constants.ERROR_RUNNING_MODES_FILE_NOT_FOUND,
            informativeText=str(e.filename),
            buttons=[_qtw.QMessageBox.Ok],
        )
    except Exception as e:
        MessageBox.create(
            messageText=constants.ERROR_RUNNING_MODES,
            informativeText=str(e),
            buttons=[_qtw.QMessageBox.Ok],
        )


def getHydraulicModesMenu(mainWindow: mw.MainWindow) -> _qtw.QMenu:  # type: ignore[name-defined]
    hydraulicModesMenu = _qtw.QMenu("Hydraulic modes", mainWindow)
    createModeTemplateAction = _qtw.QAction(
        "Create modes template", mainWindow
    )
    createModeTemplateAction.triggered.connect(
        lambda: createModesTemplate(mainWindow.project)
    )
    hydraulicModesMenu.addAction(createModeTemplateAction)

    runModesAction = _qtw.QAction("Run modes", mainWindow)
    runModesAction.triggered.connect(
        lambda: runModes(mainWindow.project, mainWindow)
    )
    hydraulicModesMenu.addAction(runModesAction)
    return hydraulicModesMenu
