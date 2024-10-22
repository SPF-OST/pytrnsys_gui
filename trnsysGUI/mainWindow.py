# type: ignore
# pylint: skip-file

import os
import pathlib as _pl
import shutil
import subprocess

import PyQt5.QtWidgets as _qtw
from collections import deque as _deque


import pytrnsys.utils.log as _ulog
import pytrnsys.utils.result as _res
import pytrnsys.utils.warnings as _warn
from PyQt5.QtWidgets import QAction

import trnsysGUI.configFileUpdater as _cfu
import trnsysGUI.diagram.export as _dexp
import trnsysGUI.loggingCallback as _lgcb
import trnsysGUI.menus.projectMenu.exportPlaceholders as _eph
from trnsysGUI import buildDck as buildDck
from trnsysGUI import images as _img
from trnsysGUI import project as _prj
from trnsysGUI import settings as _settings
from trnsysGUI import settingsDlg as _sdlg
from trnsysGUI import warningsAndErrors as _werrors
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MassFlowVisualizer import MassFlowVisualizer
from trnsysGUI.ProcessMain import ProcessMain
from trnsysGUI.RunMain import RunMain
from trnsysGUI.messageBox import MessageBox
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler
from trnsysGUI.common import cancelled as _ccl
from trnsysGUI.diagram import Editor as _de
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.constants import UNSAVED_PROGRESS_LOST


class MainWindow(_qtw.QMainWindow):
    def __init__(self, logger, project: _prj.Project, parent=None):
        super().__init__(parent)

        self.editor = None

        self.jsonPath = None
        self.logger = logger

        self.labelVisState = False
        self.calledByVisualizeMf = False
        self.currentFile = "Untitled"
        self.showBoxOnClose = True

        # Toolbar actions
        saveDiaAction = _qtw.QAction(_img.INBOX_PNG.icon(), "Save", self)
        saveDiaAction.triggered.connect(self.saveDia)

        loadDiaAction = _qtw.QAction(_img.OUTBOX_PNG.icon(), "Open", self)
        loadDiaAction.triggered.connect(self.loadDia)

        updateConfigAction = _qtw.QAction(_img.UPDATE_CONFIG_PNG.icon(), "Update run.config", self)
        updateConfigAction.triggered.connect(self.updateRun)

        runSimulationAction = _qtw.QAction(_img.RUN_SIMULATION_PNG.icon(), "Run simulation", self)
        runSimulationAction.triggered.connect(self.runSimulation)

        processSimulationAction = _qtw.QAction(_img.PROCESS_SIMULATION_PNG.icon(), "Process data", self)
        processSimulationAction.triggered.connect(self.processSimulation)

        deleteDiaAction = _qtw.QAction(_img.TRASH_PNG.icon(), "Delete diagram", self)
        deleteDiaAction.triggered.connect(self.deleteDia)

        zoomInAction = _qtw.QAction(_img.ZOOM_IN_PNG.icon(), "Zoom in", self)
        zoomInAction.triggered.connect(self.setZoomIn)

        zoomOutAction = _qtw.QAction(_img.ZOOM_OUT_PNG.icon(), "Zoom out", self)
        zoomOutAction.triggered.connect(self.setZoomOut)

        toggleConnLabels = _qtw.QAction(_img.LABEL_TOGGLE_PNG.icon(), "Toggle labels", self)
        toggleConnLabels.triggered.connect(self.toggleConnLabels)

        exportHydraulicsAction = _qtw.QAction(_img.EXPORT_HYDRAULICS_PNG.icon(), "Export hydraulic.ddck", self)
        exportHydraulicsAction.triggered.connect(self.exportHydraulicsDdck)

        exportHydCtrlAction = _qtw.QAction(
            _img.EXPORT_HYDRAULIC_CONTROL_PNG.icon(),
            "Export hydraulic_control.ddck",
            self,
        )
        exportHydCtrlAction.triggered.connect(self.exportHydraulicControl)

        exportDckAction = _qtw.QAction(_img.EXPORT_DCK_PNG.icon(), "Export dck", self)
        exportDckAction.triggered.connect(self.exportDck)

        toggleSnapAction = _qtw.QAction("Toggle snap grid", self)
        toggleSnapAction.triggered.connect(self.toggleSnap)
        toggleSnapAction.setShortcut("a")

        toggleAlignModeAction = _qtw.QAction("Toggle align mode", self)
        toggleAlignModeAction.triggered.connect(self.toggleAlignMode)
        toggleAlignModeAction.setShortcut("q")

        runMassflowSolverAction = _qtw.QAction(_img.RUN_MFS_PNG.icon(), "Run the massflow solver", self)
        runMassflowSolverAction.triggered.connect(self.runAndVisMf)

        openVisualizerAction = _qtw.QAction(_img.VIS_MFS_PNG.icon(), "Start visualization of mass flows", self)
        openVisualizerAction.triggered.connect(self.visualizeMf)

        # Tool bar
        tb = self.addToolBar("Main Toolbar...")
        tb.setObjectName("Toolbar")
        tb.addAction(saveDiaAction)
        tb.addAction(loadDiaAction)
        tb.addAction(zoomInAction)
        tb.addAction(zoomOutAction)
        tb.addAction(toggleConnLabels)
        tb.addAction(runMassflowSolverAction)
        tb.addAction(openVisualizerAction)
        tb.addAction(exportHydraulicsAction)
        tb.addAction(exportHydCtrlAction)
        tb.addAction(updateConfigAction)
        tb.addAction(exportDckAction)
        tb.addAction(runSimulationAction)
        tb.addAction(processSimulationAction)
        tb.addAction(deleteDiaAction)

        # Menu bar actions
        self.fileMenu = _qtw.QMenu("File")

        fileMenuNewAction = _qtw.QAction("New", self)
        fileMenuNewAction.triggered.connect(self.newDia)
        fileMenuNewAction.setShortcut("Ctrl+n")
        self.fileMenu.addAction(fileMenuNewAction)

        fileMenuOpenAction = _qtw.QAction("Open", self)
        fileMenuOpenAction.triggered.connect(self.openFile)
        fileMenuOpenAction.setShortcut("Ctrl+o")
        self.fileMenu.addAction(fileMenuOpenAction)

        self.recentProjectsMenu = _qtw.QMenu("Recent Projects")
        self.recentProjectsMenu.triggered.connect(self.openRecentFile)
        self.fileMenu.addMenu(self.recentProjectsMenu)
        self.updateRecentFileMenu(project.jsonFilePath)

        fileMenuSaveAction = _qtw.QAction("Save", self)
        fileMenuSaveAction.triggered.connect(self.saveDia)
        fileMenuSaveAction.setShortcut("Ctrl+s")
        self.fileMenu.addAction(fileMenuSaveAction)

        fileMenuCopyToNewAction = _qtw.QAction("Copy to new folder", self)
        fileMenuCopyToNewAction.triggered.connect(self.copyToNew)
        self.fileMenu.addAction(fileMenuCopyToNewAction)

        exportDiagram = _qtw.QAction("Export diagram", self)
        exportDiagram.triggered.connect(self.exportDiagram)
        exportDiagram.setShortcut("Ctrl+e")
        self.fileMenu.addAction(exportDiagram)

        debugConnections = _qtw.QAction("Debug Conn", self)
        debugConnections.triggered.connect(self.debugConns)
        self.fileMenu.addAction(debugConnections)

        def askForSaveAndLoadSettings() -> None:
            self.askUserForSettingsValuesAndSave()
            self.loadTrnsysPath()

        setTransysPath = _qtw.QAction("Set TRNSYS path", self)
        setTransysPath.triggered.connect(askForSaveAndLoadSettings)
        self.fileMenu.addAction(setTransysPath)

        self.editMenu = _qtw.QMenu("Edit")
        self.editMenu.addAction(toggleSnapAction)
        self.editMenu.addAction(toggleAlignModeAction)

        runMassflowSolverActionMenu = _qtw.QAction("Run mass flow solver", self)
        runMassflowSolverActionMenu.triggered.connect(self.runAndVisMf)

        openVisualizerActionMenu = _qtw.QAction("Start mass flow visualizer", self)
        openVisualizerActionMenu.triggered.connect(self.visualizeMf)

        exportHydraulicsActionMenu = _qtw.QAction("Export hydraulic.ddck", self)
        exportHydraulicsActionMenu.triggered.connect(self.exportHydraulicsDdck)

        exportHydCtrlActionMenu = _qtw.QAction("Export hydraulic_control.ddck", self)
        exportHydCtrlActionMenu.triggered.connect(self.exportHydraulicControl)

        exportDdckPlaceHolderValuesJsonFileActionMenu = _qtw.QAction("Export ddck placeholder values JSON file", self)
        exportDdckPlaceHolderValuesJsonFileActionMenu.triggered.connect(self.exportDdckPlaceHolderValuesJson)

        updateConfigActionMenu = _qtw.QAction("Update run.config", self)
        updateConfigActionMenu.triggered.connect(self.updateRun)

        exportDckActionMenu = _qtw.QAction("Export dck", self)
        exportDckActionMenu.triggered.connect(self.exportDck)

        runSimulationActionMenu = _qtw.QAction("Run simulation...", self)
        runSimulationActionMenu.triggered.connect(self.runSimulation)

        processSimulationActionMenu = _qtw.QAction("Process simulation...", self)
        processSimulationActionMenu.triggered.connect(self.processSimulation)

        self.projectMenu = _qtw.QMenu("Project")
        self.projectMenu.addAction(runMassflowSolverActionMenu)
        self.projectMenu.addAction(openVisualizerActionMenu)
        self.projectMenu.addAction(exportHydraulicsActionMenu)
        self.projectMenu.addAction(exportHydCtrlActionMenu)
        self.projectMenu.addAction(exportDdckPlaceHolderValuesJsonFileActionMenu)
        self.projectMenu.addAction(updateConfigActionMenu)
        self.projectMenu.addAction(exportDckActionMenu)
        self.projectMenu.addAction(runSimulationActionMenu)
        self.projectMenu.addAction(processSimulationActionMenu)

        pytrnsysOnlineDocAction = _qtw.QAction("pytrnsys online documentation", self)
        pytrnsysOnlineDocAction.triggered.connect(self.openPytrnsysOnlineDoc)

        self.helpMenu = _qtw.QMenu("Help")
        self.helpMenu.addAction(pytrnsysOnlineDocAction)

        # Menu bar
        self.mb = self.menuBar()
        self.mb.addMenu(self.fileMenu)
        self.mb.addMenu(self.projectMenu)
        self.mb.addMenu(self.editMenu)
        self.mb.addMenu(self.helpMenu)
        self.mb.addSeparator()

        # Status bar
        self.sb = self.statusBar()

        # QUndo framework
        self.undoStack = _qtw.QUndoStack(self)
        undoAction = self.undoStack.createUndoAction(self, "Undo")
        undoAction.setShortcut("Ctrl+z")

        redoAction = self.undoStack.createRedoAction(self, "Redo")
        redoAction.setShortcut("Ctrl+y")

        self.editMenu.addAction(undoAction)
        self.editMenu.addAction(redoAction)

        self._resetEditor(project)

    def isRunning(self):
        return self.editor.isRunning()

    def start(self) -> None:
        _lgcb.configureLoggingCallback(self.logger, self._loggingCallback, _ulog.FORMAT)
        self.editor.start()

    def shutdown(self) -> None:
        _lgcb.removeLoggingCallback(self.logger, self._loggingCallback)
        self.editor.shutdown()

    def newDia(self):
        if MessageBox.create(messageText=UNSAVED_PROGRESS_LOST) == _qtw.QMessageBox.Cancel:
            return

        startingDirectoryPath = self._projectDirPath.parent

        createProjectMaybeCancelled = _prj.getCreateProject(startingDirectoryPath)
        if _ccl.isCancelled(createProjectMaybeCancelled):
            return

        createProject = _ccl.value(createProjectMaybeCancelled)

        self.updateRecentFileMenu(createProject.jsonFilePath)
        self._resetEditor(createProject)

    def saveDia(self):
        self.logger.info("Saving diagram")
        self.editor.save()

    def copyToNew(self):
        currentProjectFolderPath = self._projectDirPath

        startingDirectoryPath = currentProjectFolderPath.parent

        maybeCancelled = _prj.getExistingEmptyDirectory(startingDirectoryPath)
        if _ccl.isCancelled(maybeCancelled):
            return
        newProjectFolderPath = _ccl.value(maybeCancelled)

        oldProjectFolderPath = self._projectDirPath

        self.copyContentsToNewFolder(newProjectFolderPath, oldProjectFolderPath)

    def copyContentsToNewFolder(self, newProjectFolderPath, oldProjectFolderPath):
        self._copyContents(oldProjectFolderPath, newProjectFolderPath)
        newJsonFilePath = self._changeAndGetNewJsonFileName(newProjectFolderPath, oldProjectFolderPath)

        loadProject = _prj.LoadProject(newJsonFilePath)

        self._resetEditor(loadProject)

        self.editor.save(showWarning=False)

    @staticmethod
    def _copyContents(oldProjectFolderPath, newProjectFolderPath):
        for child in oldProjectFolderPath.iterdir():
            destinationPath = newProjectFolderPath / child.name
            if child.is_dir():
                shutil.copytree(child, destinationPath)
            else:
                shutil.copy(child, destinationPath)

    @staticmethod
    def _changeAndGetNewJsonFileName(newProjectFolderPath, oldProjectFolderPath):
        oldJsonFileName = f"{oldProjectFolderPath.name}.json"
        newJsonFileName = f"{newProjectFolderPath.name}.json"
        shutil.move(
            newProjectFolderPath / oldJsonFileName,
            newProjectFolderPath / newJsonFileName,
        )
        newJsonFilePath = newProjectFolderPath / newJsonFileName
        return newJsonFilePath

    def loadDia(self):
        self.logger.info("Loading diagram")
        self.openFile()

    def updateRun(self):
        configFilePath = self._projectDirPath / "run.config"

        if configFilePath.is_dir():
            _qtw.QMessageBox.information(
                self,
                "`run.config` is a directory",
                f"Could not create file {configFilePath} because a directory of the same name exists. "
                "Please remove or rename the directory before trying to update the `run.config` file.",
            )
            return

        configFilePath.touch()

        runConfig = _cfu.ConfigFileUpdater(configFilePath)
        runConfig.updateConfig()

    @property
    def _projectDirPath(self) -> _pl.Path:
        return _pl.Path(self.projectFolder)

    def runSimulation(self):
        ddckPath = os.path.join(self.projectFolder, "ddck")

        #   Check hydraulic.ddck
        hydraulicPath = os.path.join(ddckPath, "hydraulic\\hydraulic.ddck")
        if not os.path.isfile(hydraulicPath):
            self.exportHydraulicsDdck()

        #   Check ddcks of storage tanks
        storageWithoutFile = []
        for object in self.editor.trnsysObj:
            if isinstance(object, StorageTank):
                storageTankFile = os.path.join(object.displayName, object.displayName + ".ddck")
                storageTankPath = os.path.join(ddckPath, storageTankFile)
                if not (os.path.isfile(storageTankPath)):
                    storageWithoutFile.append(object.displayName + "\n")

        if storageWithoutFile:
            errorMessage = "The following storage tank(s) do(es) not have a corresponding ddck:\n\n"
            for storage in storageWithoutFile:
                errorMessage += storage
            errorMessage += (
                "\nPlease make sure you that you export the ddck for every storage tank before starting a simulation."
            )
            _werrors.showMessageBox(errorMessage)
            return

        #   Update run.config
        self.updateRun()

        #   Start simulation
        runApp = RunMain()
        executionFailed, errorStatement = runApp.runAction(self.logger, self.editor.projectFolder)

        if executionFailed:
            errorMessage = f"Exception while trying to execute RunParallelTrnsys:\n\n{errorStatement}"
            _werrors.showMessageBox(errorMessage)

        return

    def processSimulation(self):
        processPath = os.path.join(self.projectFolder, "process.config")
        if not os.path.isfile(processPath):
            errorMessage = f"No such file: {processPath}"
            _werrors.showMessageBox(errorMessage)
            return
        processApp = ProcessMain()
        result = processApp.processAction(self.logger, self.editor.projectFolder)

        if _res.isError(result):
            error = _res.error(result)
            _werrors.showMessageBox(error.message)

        return

    def exportDdckPlaceHolderValuesJson(self):
        result = _eph.exportDdckPlaceHolderValuesJsonFile(self.editor)
        if _res.isError(result):
            errorMessage = f"The json file could not be generated: {result.message}"
            _werrors.showMessageBox(errorMessage)

    def renameDia(self):
        self.logger.info("Renaming diagram...")
        self.editor.showDiagramDlg()

    def deleteDia(self):
        qmb = _qtw.QMessageBox()
        qmb.setText('Are you sure you want to delete the diagram? (There is no possibility to "undo".)')
        qmb.setStandardButtons(_qtw.QMessageBox.Yes | _qtw.QMessageBox.Cancel)
        qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == _qtw.QMessageBox.Yes:
            self.logger.info("Deleting diagram")
            self.editor.delBlocks()
        else:
            self.logger.info("Canceling")
            return

    def setZoomIn(self):
        self.logger.info("Setting zoom in")
        self.editor.diagramView.scale(1.2, 1.2)

    def setZoomOut(self):
        self.logger.info("Setting zoom out")
        self.editor.diagramView.scale(0.8, 0.8)

    def setZoom0(self):
        self.logger.info("Setting zoom 0")
        self.editor.diagramView.resetTransform()

    def runAndVisMf(self):
        self.calledByVisualizeMf = True
        filePaths = self.runMassflowSolver()
        if not filePaths:
            self.logger.error("Could not execute runMassflowSolver")
            return

        mfrFile, tempFile = filePaths
        if not os.path.isfile(mfrFile) or not os.path.isfile(tempFile):
            self.logger.error("No mfrFile or tempFile found!")
            return

        MassFlowVisualizer(self, mfrFile, tempFile)

    def visualizeMf(self):
        qmb = _qtw.QMessageBox()
        qmb.setText("Please select the mass flow rate prt-file that you want to visualize.")
        qmb.setStandardButtons(_qtw.QMessageBox.Ok)
        qmb.setDefaultButton(_qtw.QMessageBox.Ok)
        qmb.exec()

        mfrFile = _qtw.QFileDialog.getOpenFileName(self, "Open diagram", filter="*Mfr.prt")[0].replace("/", "\\")
        tempFile = mfrFile.replace("Mfr", "T")
        self.calledByVisualizeMf = True
        if os.path.isfile(mfrFile) and os.path.isfile(tempFile):
            MassFlowVisualizer(self, mfrFile, tempFile)
        else:
            self.logger.info("No mfrFile or tempFile found!")

    def openFile(self):
        self.logger.info("Opening diagram")

        if MessageBox.create(messageText=UNSAVED_PROGRESS_LOST) == _qtw.QMessageBox.Cancel:
            return

        maybeCancelled = _prj.getLoadOrMigrateProject()
        if _ccl.isCancelled(maybeCancelled):
            return
        project = _ccl.value(maybeCancelled)
        RecentProjectsHandler.addProject(project.jsonFilePath)
        self.updateRecentFileMenu(project.jsonFilePath)
        self._resetEditor(project)

        if isinstance(project, _prj.MigrateProject):
            self.editor.save()

    def openRecentFile(self, actionClicked: QAction):
        if MessageBox.create(messageText=UNSAVED_PROGRESS_LOST) == _qtw.QMessageBox.Cancel:
            return

        maybeCancelled = _prj.loadRecentProject(_pl.Path(actionClicked.text()))
        if _ccl.isCancelled(maybeCancelled):
            return

        project = _ccl.value(maybeCancelled)
        RecentProjectsHandler.addProject(project.jsonFilePath)
        self.updateRecentFileMenu(project.jsonFilePath)
        self._resetEditor(project)

    def _resetEditor(self, project):
        wasRunning = self.editor and self.editor.isRunning()

        self.undoStack.clear()

        self.editor = self._createDiagramEditor(project)
        self.setCentralWidget(self.editor)

        if wasRunning:
            self.editor.start()

    def toggleConnLabels(self):
        self.labelVisState = not self.labelVisState
        self.editor.setConnLabelVis(self.labelVisState)

    def exportHydraulicsDdck(self):
        self.editor.exportHydraulics(exportTo="ddck")

    def exportHydraulicControl(self):
        self.editor.exportHydraulicControl()

    def exportDck(self):
        jsonResult = _eph.exportDdckPlaceHolderValuesJsonFile(self.editor)
        if _res.isError(jsonResult):
            errorMessage = f"The placeholder values JSON file could not be generated: {jsonResult.message}"
            _werrors.showMessageBox(errorMessage)
            return

        builder = buildDck.DckBuilder(self._projectDirPath)

        result = builder.buildTrnsysDeck()
        if _res.isError(result):
            errorMessage = f"The deck file could not be generated: {result.message}"
            _werrors.showMessageBox(errorMessage)
            return
        warnings: _warn.ValueWithWarnings[str | None] = _res.value(result)

        if warnings.hasWarnings():
            warningMessage = warnings.toWarningMessage()
            _werrors.showMessageBox(warningMessage, _werrors.Title.WARNING)

    def toggleAlignMode(self):
        self.logger.info("Toggling alignMode")
        self.editor.alignMode = not self.editor.alignMode

    def toggleSnap(self):
        self.editor.toggleSnap()

    def runMassflowSolver(self):
        self.logger.info("Running massflow solver...")

        exportPath = self.editor.exportHydraulics(exportTo="mfs")
        if not exportPath:
            return None

        self.exportedTo = exportPath
        self.logger.info(exportPath)

        if not self.editor.trnsysPath.is_file():
            errorMessage = "TRNExe.exe not found! Consider correcting the path in the settings."
            _werrors.showMessageBox(errorMessage)
            return None

        try:
            subprocess.run([str(self.editor.trnsysPath), exportPath, "/H"], check=True)
            mfrFile = os.path.join(self.projectFolder, self.projectFolder.split("\\")[-1] + "_Mfr.prt")
            tempFile = os.path.join(self.projectFolder, self.projectFolder.split("\\")[-1] + "_T.prt")
            self.calledByVisualizeMf = False
            return mfrFile, tempFile
        except Exception as exception:
            errorMessage = f"An exception occurred while trying to execute the mass flow solver: {exception}"
            _werrors.showMessageBox(errorMessage)
            self.logger.error(errorMessage)

            return None

    def movePorts(self):
        self.editor.moveDirectPorts = True

    def openPytrnsysOnlineDoc(self):
        os.system('start "" https://pytrnsys.readthedocs.io')

    def exportDiagram(self):
        fileName, _ = _qtw.QFileDialog.getSaveFileName(
            self, "Export PDF", None, "PDF files (*.pdf);;SVG files (*.svg);;All Files (*)", "PDF files (*.svg)"
        )
        if fileName == "":
            return

        if _dexp.getExtension(fileName) == "":
            fileName += ".pdf"

        _dexp.export(self.editor.diagramScene, fileName)

    def closeEvent(self, e):
        if self.showBoxOnClose:
            qmb = _qtw.QMessageBox()
            qmb.setText("Do you want to save the current state of the project before closing the program?")
            qmb.setStandardButtons(_qtw.QMessageBox.Save | _qtw.QMessageBox.Close | _qtw.QMessageBox.Cancel)
            qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == _qtw.QMessageBox.Cancel:
                e.ignore()
                return
            if ret == _qtw.QMessageBox.Save:
                self.editor.save()

            RecentProjectsHandler.save()
            e.accept()

    def ensureSettingsExist(self):
        if not _settings.Settings.tryLoadOrNone():
            self.askUserForSettingsValuesAndSave()

    def askUserForSettingsValuesAndSave(self):
        newSettings = _sdlg.SettingsDlg.showDialogAndGetSettings(parent=self)
        while newSettings == _sdlg.CANCELLED:
            newSettings = _sdlg.SettingsDlg.showDialogAndGetSettings(parent=self)
        newSettings.save()

    def loadTrnsysPath(self):
        settings = _settings.Settings.load()
        self.editor.trnsysPath = _pl.Path(settings.trnsysBinaryPath)

    def debugConns(self):
        """
        Check each block items for error connections.
        Returns warning message if blockitem contains two input connections or two output connections
        """
        self.logger.info("trnsysObjs:", self.editor.trnsysObj)
        self.noErrorConns = True
        for o in self.editor.trnsysObj:
            self.logger.info(o)
            if isinstance(o, BlockItem) and len(o.outputs) == 1 and len(o.inputs) == 1:
                self.logger.info("Checking block connections", o.displayName)
                objInput = o.inputs[0]
                objOutput = o.outputs[0]
                connToInputToPort = objInput.connectionList[0].toPort
                connToOutputToPort = objOutput.connectionList[0].toPort
                connToInputFromPort = objInput.connectionList[0].fromPort
                connToOutputFromPort = objOutput.connectionList[0].fromPort
                connName1 = objInput.connectionList[0].displayName
                connName2 = objOutput.connectionList[0].displayName
                objName = o.displayName

                if objInput == connToInputToPort and objOutput == connToOutputToPort:
                    msgBox = _qtw.QMessageBox()
                    msgBox.setText("both %s and %s are input ports into %s" % (connName1, connName2, objName))
                    msgBox.exec_()
                    self.noErrorConns = False

                elif objInput == connToInputFromPort and objOutput == connToOutputFromPort:
                    msgBox = _qtw.QMessageBox()
                    msgBox.setText("both %s and %s are output ports from %s" % (connName1, connName2, objName))
                    msgBox.exec_()
                    self.noErrorConns = False
        return self.noErrorConns

    def _createDiagramEditor(self, project: _prj.Project) -> _de.Editor:
        if isinstance(project, _prj.LoadProject):
            self.projectFolder = str(project.jsonFilePath.parent)
            return _de.Editor(
                self,
                str(project.jsonFilePath.parent),
                jsonPath=None,
                loadValue="load",
                logger=self.logger,
            )

        if isinstance(project, _prj.MigrateProject):
            self.projectFolder = str(project.newProjectFolderPath)
            return _de.Editor(
                self,
                str(project.newProjectFolderPath),
                str(project.oldJsonFilePath),
                loadValue="json",
                logger=self.logger,
            )

        if isinstance(project, _prj.CreateProject):
            self.projectFolder = str(project.jsonFilePath.parent)
            return _de.Editor(
                self,
                self.projectFolder,
                jsonPath=str(project.jsonFilePath),
                loadValue="new",
                logger=self.logger,
            )

        raise AssertionError(f"Unknown `project' type: {type(project)}")

    def _loggingCallback(self, logMessage: str) -> None:
        self.editor.loggingTextEdit.appendPlainText(logMessage)

    def updateRecentFileMenu(self, currentProject: _pl.Path):
        self.recentProjectsMenu.clear()
        for recentProject in RecentProjectsHandler.recentProjects:
            if recentProject != currentProject and recentProject.exists():
                recentProjectAction = _qtw.QAction(str(recentProject), self)
                self.recentProjectsMenu.addAction(recentProjectAction)
