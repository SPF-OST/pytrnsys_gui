# pylint: skip-file
# type: ignore

import os
import pathlib as _pl
import shutil
import subprocess
import sys

from PyQt5.QtWidgets import *
from pytrnsys.utils import log

import trnsysGUI.arguments as args
import trnsysGUI.buildDck as dckBuilder
import trnsysGUI.common.cancelled as _ccl
import trnsysGUI.common.error as _err
import trnsysGUI.diagram.Editor as _de
import trnsysGUI.images as _img
import trnsysGUI.project as _prj
import trnsysGUI.settings as _settings
import trnsysGUI.settingsDlg as _sdlg
import trnsysGUI.tracing as trc
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Connection import Connection
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.MassFlowVisualizer import MassFlowVisualizer
from trnsysGUI.ProcessMain import ProcessMain
from trnsysGUI.RunMain import RunMain
from trnsysGUI.StorageTank import StorageTank
from trnsysGUI.configFile import configFile

__version__ = "1.0.0"
__author__ = "Stefano Marti"
__email__ = "stefano.marti@spf.ch"
__status__ = "Prototype"


class _MainWindow(QMainWindow):
    def __init__(self, logger, project: _prj.Project, parent=None):
        super().__init__(parent)

        self.jsonPath = None
        self.logger = logger

        self.centralWidget = self._createDiagramEditor(project)
        self.setCentralWidget(self.centralWidget)

        self.labelVisState = False
        self.massFlowEnabled = False
        self.calledByVisualizeMf = False
        self.currentFile = "Untitled"

        # Toolbar actions
        saveDiaAction = QAction(_img.INBOX_PNG.icon(), "Save", self)
        saveDiaAction.triggered.connect(self.saveDia)

        loadDiaAction = QAction(_img.OUTBOX_PNG.icon(), "Open", self)
        loadDiaAction.triggered.connect(self.loadDia)

        updateConfigAction = QAction(
            _img.UPDATE_CONFIG_PNG.icon(), "Update run.config", self
        )
        updateConfigAction.triggered.connect(self.updateRun)

        runSimulationAction = QAction(
            _img.RUN_SIMULATION_PNG.icon(), "Run simulation", self
        )
        runSimulationAction.triggered.connect(self.runSimulation)

        processSimulationAction = QAction(
            _img.PROCESS_SIMULATION_PNG.icon(), "Process data", self
        )
        processSimulationAction.triggered.connect(self.processSimulation)

        deleteDiaAction = QAction(_img.TRASH_PNG.icon(), "Delete diagram", self)
        deleteDiaAction.triggered.connect(self.deleteDia)

        zoomInAction = QAction(_img.ZOOM_IN_PNG.icon(), "Zoom in", self)
        zoomInAction.triggered.connect(self.setZoomIn)

        zoomOutAction = QAction(_img.ZOOM_OUT_PNG.icon(), "Zoom out", self)
        zoomOutAction.triggered.connect(self.setZoomOut)

        toggleConnLabels = QAction(_img.LABEL_TOGGLE_PNG.icon(), "Toggle labels", self)
        toggleConnLabels.triggered.connect(self.toggleConnLabels)

        exportHydraulicsAction = QAction(
            _img.EXPORT_HYDRAULICS_PNG.icon(), "Export hydraulic.ddck", self
        )
        exportHydraulicsAction.triggered.connect(self.exportHydraulicsDdck)

        exportHydCtrlAction = QAction(
            _img.EXPORT_HYDRAULIC_CONTROL_PNG.icon(),
            "Export hydraulic_control.ddck",
            self,
        )
        exportHydCtrlAction.triggered.connect(self.exportHydraulicControl)

        exportDckAction = QAction(_img.EXPORT_DCK_PNG.icon(), "Export dck", self)
        exportDckAction.triggered.connect(self.exportDck)

        editGroupsAction = QAction("Edit groups/loops", self)
        editGroupsAction.triggered.connect(self.editGroups)

        selectMultipleAction = QAction("Select multiple items", self)
        selectMultipleAction.triggered.connect(self.createSelection)
        selectMultipleAction.setShortcut("s")

        toggleSnapAction = QAction("Toggle snap grid", self)
        toggleSnapAction.triggered.connect(self.toggleSnap)
        toggleSnapAction.setShortcut("a")

        toggleAlignModeAction = QAction("Toggle align mode", self)
        toggleAlignModeAction.triggered.connect(self.toggleAlignMode)
        toggleAlignModeAction.setShortcut("q")

        runMassflowSolverAction = QAction(
            _img.RUN_MFS_PNG.icon(), "Run the massflow solver", self
        )
        runMassflowSolverAction.triggered.connect(self.runAndVisMf)

        openVisualizerAction = QAction(
            _img.VIS_MFS_PNG.icon(), "Start visualization of mass flows", self
        )
        openVisualizerAction.triggered.connect(self.visualizeMf)

        trnsysList = QAction("Print trnsysObj", self)
        trnsysList.triggered.connect(self.mb_debug)

        loadVisual = QAction("Load MRF", self)
        loadVisual.triggered.connect(self.loadVisualization)

        runAction = QAction(_img.ROTATE_TO_RIGHT_PNG.icon(), "Run", self)
        runAction.triggered.connect(self.runApp)

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
        self.fileMenu = QMenu("File")

        fileMenuNewAction = QAction("New", self)
        fileMenuNewAction.triggered.connect(self.newDia)
        fileMenuNewAction.setShortcut("Ctrl+n")
        self.fileMenu.addAction(fileMenuNewAction)

        fileMenuOpenAction = QAction("Open", self)
        fileMenuOpenAction.triggered.connect(self.openFile)
        fileMenuOpenAction.setShortcut("Ctrl+o")
        self.fileMenu.addAction(fileMenuOpenAction)

        fileMenuSaveAction = QAction("Save", self)
        fileMenuSaveAction.triggered.connect(self.saveDia)
        fileMenuSaveAction.setShortcut("Ctrl+s")
        self.fileMenu.addAction(fileMenuSaveAction)

        fileMenuCopyToNewAction = QAction("Copy to new folder", self)
        fileMenuCopyToNewAction.triggered.connect(self.copyToNew)
        self.fileMenu.addAction(fileMenuCopyToNewAction)

        exportAsPDF = QAction("Export as PDF", self)
        exportAsPDF.triggered.connect(self.exportPDF)
        exportAsPDF.setShortcut("Ctrl+e")
        self.fileMenu.addAction(exportAsPDF)

        debugConnections = QAction("Debug Conn", self)
        debugConnections.triggered.connect(self.debugConns)
        self.fileMenu.addAction(debugConnections)

        setTransysPath = QAction("Set TRNSYS path", self)
        setTransysPath.triggered.connect(self.askUserForSettingsValuesAndSave)
        self.fileMenu.addAction(setTransysPath)

        self.editMenu = QMenu("Edit")
        self.editMenu.addAction(toggleSnapAction)
        self.editMenu.addAction(toggleAlignModeAction)

        AboutAction = QAction("About", self)
        AboutAction.triggered.connect(self.showAbout)

        VersionAction = QAction("Version", self)
        VersionAction.triggered.connect(self.showVersion)

        CreditsAction = QAction("Credits", self)
        CreditsAction.triggered.connect(self.showCredits)

        self.helpMenu = QMenu("Help")
        self.helpMenu.addAction(AboutAction)
        self.helpMenu.addAction(VersionAction)
        self.helpMenu.addAction(CreditsAction)

        # Menu bar
        self.mb = self.menuBar()
        self.mb.addMenu(self.fileMenu)
        self.mb.addMenu(self.editMenu)
        self.mb.addMenu(self.helpMenu)
        self.mb.addSeparator()

        # Status bar
        self.sb = self.statusBar()
        self.sb.showMessage("Mode is " + str(self.centralWidget.editorMode))

        # QUndo framework
        self.undoStack = QUndoStack(self)
        undoAction = self.undoStack.createUndoAction(self, "Undo")
        undoAction.setShortcut("Ctrl+z")

        redoAction = self.undoStack.createRedoAction(self, "Redo")
        redoAction.setShortcut("Ctrl+y")

        self.editMenu.addAction(undoAction)
        self.editMenu.addAction(redoAction)

    def newDia(self):
        messageBox = QMessageBox()
        messageBox.setText(
            "Are you sure you want to start a new project? Unsaved progress on the current one will be lost."
        )
        messageBox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        messageBox.setDefaultButton(QMessageBox.Cancel)

        result = messageBox.exec()
        if result == QMessageBox.Cancel:
            return

        startingDirectoryPath = _pl.Path(self.projectFolder).parent

        createProjectMaybeCancelled = _prj.getCreateProject(startingDirectoryPath)
        if _ccl.isCancelled(createProjectMaybeCancelled):
            return
        createProject = _ccl.value(createProjectMaybeCancelled)

        self.centralWidget = self._createDiagramEditor(createProject)
        self.setCentralWidget(self.centralWidget)

    def saveDia(self):
        self.logger.info("Saving diagram")
        self.centralWidget.save()

    def copyToNew(self):
        currentProjectFolderPath = _pl.Path(self.projectFolder)

        startingDirectoryPath = currentProjectFolderPath.parent

        maybeCancelled = _prj.getExistingEmptyDirectory(startingDirectoryPath)
        if _ccl.isCancelled(maybeCancelled):
            return
        newProjectFolderPath = _ccl.value(maybeCancelled)

        oldProjectFolderPath = _pl.Path(self.projectFolder)

        self._copyContents(oldProjectFolderPath, newProjectFolderPath)
        newJsonFilePath = self._changeAndGetNewJsonFileName(newProjectFolderPath, oldProjectFolderPath)

        loadProject = _prj.LoadProject(newJsonFilePath)

        self.centralWidget = self._createDiagramEditor(loadProject)
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.save(showWarning=False)

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
        runConfig = configFile(configPath, self.centralWidget)
        runConfig.updateConfig()

    def runSimulation(self):
        ddckPath = os.path.join(self.projectFolder, "ddck")

        #   Check hydraulic.ddck
        hydraulicPath = os.path.join(ddckPath, "hydraulic\\hydraulic.ddck")
        if not os.path.isfile(hydraulicPath):
            self.exportHydraulicsDdck()
        infile = open(hydraulicPath, "r")
        hydraulicLines = infile.readlines()
        blackBoxLines = []
        for i in range(len(hydraulicLines)):
            if "Black box component temperatures" in hydraulicLines[i]:
                j = i + 1
                while hydraulicLines[j] != "\n":
                    blackBoxLines.append(hydraulicLines[j])
                    j += 1
                break
        messageText = "Is this correct?\n\n"
        for line in blackBoxLines:
            messageText += line
        qmb = QMessageBox()
        qmb.setText(messageText)
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        qmb.setDefaultButton(QMessageBox.No)
        ret = qmb.exec()
        if ret == QMessageBox.No:
            qmb = QMessageBox()
            qmb.setText(
                "Please make sure the black box component temperatures are correct in hydraulic.ddck before starting a simluation."
            )
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return

        #   Check ddcks of storage tanks
        storageWithoutFile = []
        for object in self.centralWidget.trnsysObj:
            if isinstance(object, StorageTank):
                storageTankFile = os.path.join(
                    object.displayName, object.displayName + ".ddck"
                )
                storageTankPath = os.path.join(ddckPath, storageTankFile)
                if not (os.path.isfile(storageTankPath)):
                    storageWithoutFile.append(object.displayName + "\n")

        if storageWithoutFile:
            messageText = "The following storage tank(s) do(es) not have a corresponding ddck:\n\n"
            for storage in storageWithoutFile:
                messageText += storage
            messageText += "\nPlease make sure you that you export the ddck for every storage tank before starting a simulation."
            qmb = QMessageBox()
            qmb.setText(messageText)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return

        #   Update run.config
        self.updateRun()

        #   Start simulation
        runApp = RunMain()
        executionFailed, errorStatement = runApp.runAction(
            self.logger, self.centralWidget.projectFolder
        )

        if executionFailed:
            messageText = (
                "Exception while trying to execute RunParallelTrnsys:\n\n"
                + errorStatement
            )
            qmb = QMessageBox()
            qmb.setText(messageText)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()

        return

    def processSimulation(self):
        processPath = os.path.join(self.projectFolder, "process.config")
        if not os.path.isfile(processPath):
            messageText = "No such file:\n" + processPath
            qmb = QMessageBox()
            qmb.setText(messageText)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return
        processApp = ProcessMain()
        executionFailed, errorStatement = processApp.processAction(
            self.logger, self.centralWidget.projectFolder
        )

        if executionFailed:
            messageText = (
                "Exception while trying to execute RunParallelTrnsys:\n\n"
                + errorStatement
            )
            qmb = QMessageBox()
            qmb.setText(messageText)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()

        return

    def renameDia(self):
        self.logger.info("Renaming diagram...")
        self.centralWidget.showDiagramDlg()

    def deleteDia(self):
        qmb = QMessageBox()
        qmb.setText(
            'Are you sure you want to delete the diagram? (There is no possibility to "undo".)'
        )
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == QMessageBox.Yes:
            self.logger.info("Deleting diagram")
            self.centralWidget.delBlocks()
        else:
            self.logger.info("Canceling")
            return

    def createGroup(self):
        # print("Tb createGroup pressed")
        # global selectionMode
        self.centralWidget.selectionMode = True
        self.centralWidget.groupMode = True
        self.centralWidget.copyMode = False
        self.centralWidget.multipleSelectMode = False

    def tidyUp(self):
        self.logger.info("Tidying up...")
        self.centralWidget.cleanUpConnections()

    def setZoomIn(self):
        self.logger.info("Setting zoom in")
        self.centralWidget.diagramView.scale(1.2, 1.2)

    def setZoomOut(self):
        self.logger.info("Setting zoom out")
        self.centralWidget.diagramView.scale(0.8, 0.8)

    def setZoom0(self):
        self.logger.info("Setting zoom 0")
        self.centralWidget.diagramView.resetTransform()

    def copySelection(self):
        self.logger.info("Copying selection")
        # global selectionMode
        # global copyMode

        self.centralWidget.selectionMode = True
        self.centralWidget.copyMode = True
        self.centralWidget.groupMode = False
        self.centralWidget.multipleSelectMode = False

        self.centralWidget.copyElements()

    def pasteSelection(self):
        self.logger.info("Pasting selection")
        self.centralWidget.pasteFromClipBoard()
        # global copyMode
        self.centralWidget.copyMode = False

    def editGroups(self):
        self.centralWidget.editGroups()

    def mb_debug(self):
        pass
        # print(self.centralWidget.trnsysObj)
        # a = [int(s.id) for s in self.centralWidget.trnsysObj]
        # a.sort()
        # print(a)
        #
        # for s in self.centralWidget.trnsysObj:
        #     if s.id == 11:
        #         print("Duplicate id obj is " + str(s.displayName) + " " + str(s.id))
        #
        # for t in self.centralWidget.trnsysObj:
        #     t.alignMode = True
        #     print(t.alignMode)

        # temp = []
        # for t in self.centralWidget.trnsysObj:
        #     if isinstance(t, BlockItem):
        #         for p in t.inputs + t.outputs:
        #             if p not in temp:
        #                 temp.append(p)
        #
        # for p in temp:
        #     if p.isFromHx:
        #         print("Port with parent " + str(p.parent.displayName) + "is from Hx")
        #
        # res = True
        #
        # for b in self.centralWidget.trnsysObj:
        #     if isinstance(b, Connection) and b not in self.centralWidget.connectionList:
        #         res = False
        #
        # print("editor connectionList is consistent with trnsysObj: " + str(res))

        # dIns = DeepInspector(self.centralWidget)

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
        self.massFlowEnabled = True

    def visualizeMf(self):
        qmb = QMessageBox()
        qmb.setText(
            "Please select the mass flow rate prt-file that you want to visualize."
        )
        qmb.setStandardButtons(QMessageBox.Ok)
        qmb.setDefaultButton(QMessageBox.Ok)
        qmb.exec()

        mfrFile = QFileDialog.getOpenFileName(self, "Open diagram", filter="*Mfr.prt")[
            0
        ].replace("/", "\\")
        tempFile = mfrFile.replace("Mfr", "T")
        self.calledByVisualizeMf = True
        if os.path.isfile(mfrFile) and os.path.isfile(tempFile):
            MassFlowVisualizer(self, mfrFile, tempFile)
            self.massFlowEnabled = True
        else:
            self.logger.info("No mfrFile or tempFile found!")

    def openFile(self):
        self.logger.info("Opening diagram")
        qmb = QMessageBox()
        qmb.setText(
            "Are you sure you want to open another project? Unsaved progress on the current one will be lost."
        )
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()

        if ret == QMessageBox.Cancel:
            return

        maybeCancelled = _prj.getLoadOrMigrateProject()
        if _ccl.isCancelled(maybeCancelled):
            return
        project = _ccl.value(maybeCancelled)

        self.centralWidget = self._createDiagramEditor(project)
        self.setCentralWidget(self.centralWidget)

    def toggleConnLabels(self):
        self.labelVisState = not self.labelVisState
        self.centralWidget.setConnLabelVis(self.labelVisState)

    def exportHydraulicsDdck(self):
        statusQuo = self.labelVisState
        if not statusQuo:
            self.toggleConnLabels()
        self.centralWidget.exportHydraulics(exportTo="ddck")
        if not statusQuo:
            self.toggleConnLabels()

    def exportHydraulicControl(self):
        self.centralWidget.exportHydraulicControl()

    def exportDck(self):
        dckBuilder.buildDck(self.projectFolder)

    def toggleEditorMode(self):
        self.logger.info("Toggling editor mode")
        self.centralWidget.editorMode = (self.centralWidget.editorMode + 1) % 2
        self.sb.showMessage("Mode is " + str(self.centralWidget.editorMode))

    def toggleAlignMode(self):
        self.logger.info("Toggling alignMode")
        self.centralWidget.alignMode = not self.centralWidget.alignMode

    def toggleSnap(self):
        self.centralWidget.snapGrid = not self.centralWidget.snapGrid
        self.centralWidget.diagramScene.update()

    def createSelection(self):
        self.centralWidget.clearSelectionGroup()
        self.centralWidget.selectionMode = True
        self.centralWidget.copyMode = False
        self.centralWidget.groupMode = False
        self.centralWidget.multipleSelectMode = True

    def deleteMultiple(self):
        # print("pressed del")
        temp = []
        self.logger.info("Child Items")
        self.logger.info(self.centralWidget.selectionGroupList.childItems())

        for t in self.centralWidget.selectionGroupList.childItems():
            temp.append(t)
            self.centralWidget.selectionGroupList.removeFromGroup(t)

        for t in temp:
            if isinstance(t, BlockItem):
                t.deleteBlock()
            elif isinstance(t, Connection):
                t.deleteConn()
            elif isinstance(t, GraphicalItem):
                t.deleteBlock()
            else:
                self.logger.info("Neiter a Block nor Connection in copyGroupList ")

    def runMassflowSolver(self):
        self.logger.info("Running massflow solver...")

        exportPath = self.centralWidget.exportHydraulics(exportTo="mfs")
        self.exportedTo = exportPath
        self.logger.info(exportPath)
        if exportPath != "None":
            msgb = QMessageBox(self)
            if not self.centralWidget.trnsysPath.is_file():
                msgb.setText(
                    "TRNExe.exe not found! Consider correcting the path in the settings."
                )
                msgb.exec()
                return 0, 0
            self.logger.info("trnsyspath: %s", self.centralWidget.trnsysPath)
            # cmd = f"{self.centralWidget.trnsysPath} {exportPath} /H"
            errorStatement = ""
            try:
                subprocess.run(
                    [str(self.centralWidget.trnsysPath), exportPath, "/H"], check=True
                )
                mfrFile = os.path.join(
                    self.projectFolder, self.projectFolder.split("\\")[-1] + "_Mfr.prt"
                )
                tempFile = os.path.join(
                    self.projectFolder, self.projectFolder.split("\\")[-1] + "_T.prt"
                )
                self.calledByVisualizeMf = False
                return mfrFile, tempFile
            except ValueError as e:
                self.logger.error("EXCEPTION WHILE TRYING TO EXECUTE RunParallelTrnsys")
                for words in e.args:
                    errorStatement += str(words)
            except OSError as e:
                self.logger.error("EXCEPTION WHILE TRYING TO EXECUTE RunParallelTrnsys")
                errorStatement = str(e)
            except:
                self.logger.error(
                    "UNDEFINED EXCEPTION WHILE TRYING TO EXECUTE RunParallelTrnsys"
                )

            messageText = (
                "Exception while trying to execute runMassflowSolver:\n\n"
                + errorStatement
            )
            qmb = QMessageBox()
            qmb.setText(messageText)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()

            return None

    def loadVisualization(self):
        MfrFile = QFileDialog.getOpenFileName(
            self, "Select Mfr File", "exports", filter="*_Mfr.prt"
        )[0]
        if MfrFile == "":
            msgb = QMessageBox(self)
            msgb.setText("No Mfr file chosen!")
            msgb.exec()
            return
        TempFile = QFileDialog.getOpenFileName(
            self, "Select Temperature File", "exports", filter="*_T.prt"
        )[0]
        if TempFile == "":
            msgb = QMessageBox(self)
            msgb.setText("No Temperature file chosen!")
            msgb.exec()
            return

        selectedMfrFileName = str(MfrFile).split("/")[-1][:-8]
        selectedTempFileName = str(TempFile).split("/")[-1][:-6]

        currentFilePath = self.currentFile
        if "\\" in currentFilePath:
            diaName = currentFilePath.split("\\")[-1][:-5]
        elif "/" in currentFilePath:
            diaName = currentFilePath.split("/")[-1][:-5]
        else:
            diaName = currentFilePath

        if selectedMfrFileName == selectedTempFileName == diaName:
            MassFlowVisualizer(self, MfrFile, TempFile)
            self.massFlowEnabled = True
        else:
            self.logger.info(selectedMfrFileName, selectedTempFileName, diaName)
            msgb = QMessageBox(self)
            msgb.setText(
                "MFR or Temperature file does not correspond to current diagram!"
            )
            msgb.exec()

    def movePorts(self):
        self.centralWidget.moveDirectPorts = True

    def mouseMoveEvent(self, e):
        pass
        # x = e.x()
        # y = e.y()
        #
        # text = "x: {0},  y: {1}".format(x, y)
        # self.sb.showMessage(text)
        # #print("event")

    def showAbout(self):
        msgb = QMessageBox(self)
        msgb.setText("PyQt based diagram editor coupled to Trnsys functions")
        msgb.exec()

    def showVersion(self):
        msgb = QMessageBox(self)
        msgb.setText(
            "Currrent version is " + __version__ + " with status " + __status__
        )
        msgb.exec()

    def showCredits(self):
        msgb = QMessageBox(self)
        msgb.setText(
            "<p><b>Contributors:</b></p>"
            "<p>Stefano Marti, Dani Carbonell, Mattia Battaglia, Jeremias Schmidli, and Martin Neugebauer."
        )
        # "Icons made by Jeremias Schmidli and with icons by Vaadin from  www.flaticon.com</p>"
        msgb.exec()

    def exportPDF(self):
        self.centralWidget.printPDF()

    def closeEvent(self, e):
        qmb = QMessageBox()
        qmb.setText(
            "Do you want to save the current state of the project before closing the program?"
        )
        qmb.setStandardButtons(
            QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel
        )
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == QMessageBox.Cancel:
            e.ignore()
        elif ret == QMessageBox.Close:
            e.accept()
        elif ret == QMessageBox.Save:
            self.centralWidget.save()
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
        self.centralWidget.trnsysPath = _pl.Path(settings.trnsysBinaryPath)

    def debugConns(self):
        """
        Check each block items for error connections.
        Returns warning message if blockitem contains two input connections or two output connections
        """
        self.logger.info("trnsysObjs:", self.centralWidget.trnsysObj)
        self.noErrorConns = True
        for o in self.centralWidget.trnsysObj:
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
                    msgBox = QMessageBox()
                    msgBox.setText(
                        "both %s and %s are input ports into %s"
                        % (connName1, connName2, objName)
                    )
                    msgBox.exec_()
                    self.noErrorConns = False

                elif (
                    objInput == connToInputFromPort
                    and objOutput == connToOutputFromPort
                ):
                    msgBox = QMessageBox()
                    msgBox.setText(
                        "both %s and %s are output ports from %s"
                        % (connName1, connName2, objName)
                    )
                    msgBox.exec_()
                    self.noErrorConns = False
        return self.noErrorConns

    def runApp(self):
        runApp = RunMain()
        if self.centralWidget.projectPath == "":
            self.logger.info("Temp path:", self.centralWidget.projectFolder)
            runApp.runAction(self.centralWidget.projectFolder)
        else:
            self.logger.info("Project path:", self.centralWidget.projectPath)
            runApp.runAction(self.centralWidget.projectPath)

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
            editor = _de.Editor(
                self,
                str(project.newProjectFolderPath),
                str(project.oldJsonFilePath),
                loadValue="json",
                logger=self.logger,
            )
            editor.save()
            return editor

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


def main():
    arguments = args.getArgsOrExit()

    logger = log.setup_custom_logger("root", arguments.logLevel)
    app = QApplication(sys.argv)
    app.setApplicationName("Diagram Creator")

    maybeCancelled = _prj.getProject()
    if _ccl.isCancelled(maybeCancelled):
        return
    project = _ccl.value(maybeCancelled)

    form = _MainWindow(logger, project)
    form.showMaximized()
    form.show()
    form.ensureSettingsExist()
    form.loadTrnsysPath()

    tracer = trc.createTracer(arguments.shallTrace)
    tracer.run(lambda: app.exec())


if __name__ == "__main__":
    main()
