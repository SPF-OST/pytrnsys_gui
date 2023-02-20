# type: ignore
# pylint: skip-file

import os
import pathlib as _pl
import shutil
import subprocess

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.log as _ulog
import pytrnsys.utils.result as _res
import trnsysGUI.loggingCallback as _lgcb
from trnsysGUI import (
    project as _prj,
    images as _img,
    errors as _err,
    buildDck as buildDck,
    settings as _settings,
    settingsDlg as _sdlg,
)
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MassFlowVisualizer import MassFlowVisualizer
from trnsysGUI.ProcessMain import ProcessMain
from trnsysGUI.RunMain import RunMain
from trnsysGUI.common import cancelled as _ccl
from trnsysGUI.configFile import configFile
from trnsysGUI.diagram import Editor as _de
from trnsysGUI.storageTank.widget import StorageTank


class MainWindow(_qtw.QMainWindow):
    def __init__(self, logger, project: _prj.Project, parent=None):
        super().__init__(parent)

        self.jsonPath = None
        self.logger = logger

        self.editor = self._createDiagramEditor(project)
        self.setCentralWidget(self.editor)

        _lgcb.configureLoggingCallback(self.logger, self._loggingCallback, _ulog.FORMAT)

        self.labelVisState = False
        self.calledByVisualizeMf = False
        self.currentFile = "Untitled"

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

        fileMenuSaveAction = _qtw.QAction("Save", self)
        fileMenuSaveAction.triggered.connect(self.saveDia)
        fileMenuSaveAction.setShortcut("Ctrl+s")
        self.fileMenu.addAction(fileMenuSaveAction)

        fileMenuCopyToNewAction = _qtw.QAction("Copy to new folder", self)
        fileMenuCopyToNewAction.triggered.connect(self.copyToNew)
        self.fileMenu.addAction(fileMenuCopyToNewAction)

        exportAsPDF = _qtw.QAction("Export as PDF", self)
        exportAsPDF.triggered.connect(self.exportPDF)
        exportAsPDF.setShortcut("Ctrl+e")
        self.fileMenu.addAction(exportAsPDF)

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

        updateConfigActionMenu = _qtw.QAction("Update run.config", self)
        updateConfigActionMenu.triggered.connect(self.updateRun)

        exportDckActionMenu = _qtw.QAction("Export dck", self)
        exportDckActionMenu.triggered.connect(self.exportDck)

        runSimulationActionMenu = _qtw.QAction("Run simulation...", self)
        runSimulationActionMenu.triggered.connect(self.runSimulation)

        processSimulationActionMenu = _qtw.QAction("Process simulation...", self)
        processSimulationActionMenu.triggered.connect(self.processSimulation)

        exportDdckPlaceHolderValuesJsonFileActionMenu = _qtw.QAction(
            "Export json-file containing connection information", self
        )
        exportDdckPlaceHolderValuesJsonFileActionMenu.triggered.connect(self.exportDdckPlaceHolderValuesJson)

        self.projectMenu = _qtw.QMenu("Project")
        self.projectMenu.addAction(runMassflowSolverActionMenu)
        self.projectMenu.addAction(openVisualizerActionMenu)
        self.projectMenu.addAction(exportHydraulicsActionMenu)
        self.projectMenu.addAction(exportHydCtrlActionMenu)
        self.projectMenu.addAction(updateConfigActionMenu)
        self.projectMenu.addAction(exportDckActionMenu)
        self.projectMenu.addAction(runSimulationActionMenu)
        self.projectMenu.addAction(processSimulationActionMenu)
        self.projectMenu.addAction(exportDdckPlaceHolderValuesJsonFileActionMenu)

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
        self.sb.showMessage("Mode is " + str(self.editor.editorMode))

        # QUndo framework
        self.undoStack = _qtw.QUndoStack(self)
        undoAction = self.undoStack.createUndoAction(self, "Undo")
        undoAction.setShortcut("Ctrl+z")

        redoAction = self.undoStack.createRedoAction(self, "Redo")
        redoAction.setShortcut("Ctrl+y")

        self.editMenu.addAction(undoAction)
        self.editMenu.addAction(redoAction)

    def newDia(self):
        messageBox = _qtw.QMessageBox()
        messageBox.setText(
            "Are you sure you want to start a new project? Unsaved progress on the current one will be lost."
        )
        messageBox.setStandardButtons(_qtw.QMessageBox.Yes | _qtw.QMessageBox.Cancel)
        messageBox.setDefaultButton(_qtw.QMessageBox.Cancel)

        result = messageBox.exec()
        if result == _qtw.QMessageBox.Cancel:
            return

        startingDirectoryPath = _pl.Path(self.projectFolder).parent

        createProjectMaybeCancelled = _prj.getCreateProject(startingDirectoryPath)
        if _ccl.isCancelled(createProjectMaybeCancelled):
            return
        createProject = _ccl.value(createProjectMaybeCancelled)

        self.editor = self._createDiagramEditor(createProject)
        self.setCentralWidget(self.editor)

    def saveDia(self):
        self.logger.info("Saving diagram")
        self.editor.save()

    def copyToNew(self):
        currentProjectFolderPath = _pl.Path(self.projectFolder)

        startingDirectoryPath = currentProjectFolderPath.parent

        maybeCancelled = _prj.getExistingEmptyDirectory(startingDirectoryPath)
        if _ccl.isCancelled(maybeCancelled):
            return
        newProjectFolderPath = _ccl.value(maybeCancelled)

        oldProjectFolderPath = _pl.Path(self.projectFolder)

        self.copyContentsToNewFolder(newProjectFolderPath, oldProjectFolderPath)

    def copyContentsToNewFolder(self, newProjectFolderPath, oldProjectFolderPath):
        self._copyContents(oldProjectFolderPath, newProjectFolderPath)
        newJsonFilePath = self._changeAndGetNewJsonFileName(newProjectFolderPath, oldProjectFolderPath)

        loadProject = _prj.LoadProject(newJsonFilePath)

        self.editor = self._createDiagramEditor(loadProject)
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
        self.logger.info("Updating run.config")
        configPath = os.path.join(self.projectFolder, "run.config")
        runConfig = configFile(configPath, self.editor)
        runConfig.updateConfig()

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
            _err.showErrorMessageBox(errorMessage)
            return

        #   Update run.config
        self.updateRun()

        #   Start simulation
        runApp = RunMain()
        executionFailed, errorStatement = runApp.runAction(self.logger, self.editor.projectFolder)

        if executionFailed:
            errorMessage = f"Exception while trying to execute RunParallelTrnsys:\n\n{errorStatement}"
            _err.showErrorMessageBox(errorMessage)

        return

    def processSimulation(self):
        processPath = os.path.join(self.projectFolder, "process.config")
        if not os.path.isfile(processPath):
            errorMessage = f"No such file: {processPath}"
            _err.showErrorMessageBox(errorMessage)
            return
        processApp = ProcessMain()
        result = processApp.processAction(self.logger, self.editor.projectFolder)

        if _res.isError(result):
            error = _res.error(result)
            _err.showErrorMessageBox(error.message)

        return

    def exportDdckPlaceHolderValuesJson(self):
        result = self.editor.exportDdckPlaceHolderValuesJsonFile()
        if _res.isError(result):
            errorMessage = f"The json file could not be generated: {result.message}"
            _err.showErrorMessageBox(errorMessage)

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

    def tidyUp(self):
        self.logger.info("Tidying up...")
        self.editor.cleanUpConnections()

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
        qmb = _qtw.QMessageBox()
        qmb.setText("Are you sure you want to open another project? Unsaved progress on the current one will be lost.")
        qmb.setStandardButtons(_qtw.QMessageBox.Yes | _qtw.QMessageBox.Cancel)
        qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
        ret = qmb.exec()

        if ret == _qtw.QMessageBox.Cancel:
            return

        maybeCancelled = _prj.getLoadOrMigrateProject()
        if _ccl.isCancelled(maybeCancelled):
            return
        project = _ccl.value(maybeCancelled)

        self.editor = self._createDiagramEditor(project)
        self.setCentralWidget(self.editor)

        if isinstance(self.editor, _prj.MigrateProject):
            self.editor.save()

    def toggleConnLabels(self):
        self.labelVisState = not self.labelVisState
        self.editor.setConnLabelVis(self.labelVisState)

    def exportHydraulicsDdck(self):
        self.editor.exportHydraulics(exportTo="ddck")

    def exportHydraulicControl(self):
        self.editor.exportHydraulicControl()

    def exportDck(self):
        jsonResult = self.editor.exportDdckPlaceHolderValuesJsonFile()
        if _res.isError(jsonResult):
            errorMessage = f"The placeholder values JSON file could not be generated: {jsonResult.message}"
            _err.showErrorMessageBox(errorMessage)
            return

        builder = buildDck.buildDck(self.projectFolder)

        result = builder.buildTrnsysDeck()
        if _res.isError(result):
            errorMessage = f"The deck file could not be generated: {result.message}"
            _err.showErrorMessageBox(errorMessage)

    def toggleEditorMode(self):
        self.logger.info("Toggling editor mode")
        self.editor.editorMode = (self.editor.editorMode + 1) % 2
        self.sb.showMessage("Mode is " + str(self.editor.editorMode))

    def toggleAlignMode(self):
        self.logger.info("Toggling alignMode")
        self.editor.alignMode = not self.editor.alignMode

    def toggleSnap(self):
        self.editor.snapGrid = not self.editor.snapGrid
        self.editor.diagramScene.update()

    def runMassflowSolver(self):
        self.logger.info("Running massflow solver...")

        exportPath = self.editor.exportHydraulics(exportTo="mfs")
        if not exportPath:
            return None

        self.exportedTo = exportPath
        self.logger.info(exportPath)

        if not self.editor.trnsysPath.is_file():
            errorMessage = "TRNExe.exe not found! Consider correcting the path in the settings."
            _err.showErrorMessageBox(errorMessage)
            return None

        try:
            subprocess.run([str(self.editor.trnsysPath), exportPath, "/H"], check=True)
            mfrFile = os.path.join(self.projectFolder, self.projectFolder.split("\\")[-1] + "_Mfr.prt")
            tempFile = os.path.join(self.projectFolder, self.projectFolder.split("\\")[-1] + "_T.prt")
            self.calledByVisualizeMf = False
            return mfrFile, tempFile
        except Exception as exception:
            errorMessage = f"An exception occurred while trying to execute the mass flow solver: {exception}"
            _err.showErrorMessageBox(errorMessage)
            self.logger.error(errorMessage)

            return None

    def movePorts(self):
        self.editor.moveDirectPorts = True

    def mouseMoveEvent(self, e):
        pass

    def openPytrnsysOnlineDoc(self):
        os.system('start "" https://pytrnsys.readthedocs.io')

    def exportPDF(self):
        self.editor.printPDF()

    def closeEvent(self, e):
        qmb = _qtw.QMessageBox()
        qmb.setText("Do you want to save the current state of the project before closing the program?")
        qmb.setStandardButtons(_qtw.QMessageBox.Save | _qtw.QMessageBox.Close | _qtw.QMessageBox.Cancel)
        qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == _qtw.QMessageBox.Cancel:
            e.ignore()
        elif ret == _qtw.QMessageBox.Close:
            e.accept()
        elif ret == _qtw.QMessageBox.Save:
            self.editor.save()
            e.accept

    def ensureSettingsExist(self):
        settings = _settings.Settings.tryLoadOrNone()
        if not settings:
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
