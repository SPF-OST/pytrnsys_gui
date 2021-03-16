#!/usr/bin/python
import glob
import os
import shutil
import sys
from math import sqrt

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from pytrnsys.utils import log

import trnsysGUI.diagram.Editor as _de
import trnsysGUI.arguments as args
import trnsysGUI.buildDck as dckBuilder
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Connection import Connection
from trnsysGUI.FolderSetUp import FolderSetUp
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.MassFlowVisualizer import MassFlowVisualizer
from trnsysGUI.PathSetUp import PathSetUp
from trnsysGUI.ProcessMain import ProcessMain
from trnsysGUI.RunMain import RunMain
from trnsysGUI.StorageTank import StorageTank
import trnsysGUI.tracing as trc
from trnsysGUI.configFile import configFile
from trnsysGUI.settingsDlg import settingsDlg

__version__ = "1.0.0"
__author__ = "Stefano Marti"
__email__ = "stefano.marti@spf.ch"
__status__ = "Prototype"


def calcDist(p1, p2):
    """

    Parameters
    ----------
    p1 : :obj: `QPointF`

    p2 : :obj: `QPointF`

    Returns
    -------

    """
    vec = p1 - p2
    norm = sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class NewOrLoadWindow(QMessageBox):
    """
        This class represents a dialogue box that is shown when starting the GUI. It asks the user whether a new
        project should be opened or if an existing one should be loaded. Its parent class is QMessageBox.
    """

    def __init__(self, parent=None):
        QMessageBox.__init__(self, parent)
        self.setWindowTitle("Initializing options")

        self.addButton(QPushButton("New"), QMessageBox.YesRole)
        self.addButton(QPushButton("Open"), QMessageBox.NoRole)
        self.addButton(QPushButton("Cancel"), QMessageBox.RejectRole)


class MainWindow(QMainWindow):
    """
    This is the class containing the entire GUI window

    It has a menubar, a central widget and a message bar at the bottom. The central widget is
    the QWidget subclass containing the items library, the diagram editor and the element inspector
    listview.

    QActions comprise an icon (optionally), a description (tool tip) and the parent widget
    They are connected to a method via the Signals-and-Slots framework, allowing the execution of functions by an event.
    Shortcuts can be assigned to QActions.
    They get included into the application either by being added to a menu or a tool bar.

    Attributes
    ----------
    loadValue : str
        Indicates whether a new project was created, an old one loaded or the process was cancelled
    centralWidget : DiagramEditor

    labelVisState : bool

    massFlowEnabled : bool

    calledByVisualizeMf : bool

    currentFile : str
        Probably obsolete (NEM 07.10.2020)
    fileMenu : QMenu

    editMenu : QMenu

    helpMenu : QMenu

    """

    def __init__(self, logger, parent=None):
        super(MainWindow, self).__init__(parent)

        self.loadValue = ''
        self.logger = logger

        qmb = NewOrLoadWindow(self)
        qmb.setText("Do you want to start a new project or open an existing one?")
        ret = qmb.exec()

        if ret == 1:
            self.logger.info("Opening load dialogue")
            self.loadDialogue()
            if self.loadValue == 'json':
                ret = 0
            elif self.loadValue == 'cancel':
                ret = 2

        if ret == 0:
            if self.loadValue != 'json':
                self.loadValue = 'new'
            self.logger.info("Setting up new project")
            pathDialog = FolderSetUp(self)
            self.projectFolder = pathDialog.projectFolder

        if ret == 2:
            self.logger.info("Cancelled opening or loading a project")
            self.loadValue = 'cancel'

        self.centralWidget = self._createDiagramEditor()
        self.setCentralWidget(self.centralWidget)
        if self.loadValue == 'json':
            self.centralWidget.save()
        self.labelVisState = False
        self.massFlowEnabled = False
        self.calledByVisualizeMf = False
        self.currentFile = 'Untitled'

        # Toolbar actions
        saveDiaAction = QAction(QIcon('images/inbox.png'), "Save", self)
        saveDiaAction.triggered.connect(self.saveDia)

        loadDiaAction = QAction(QIcon('images/outbox.png'), "Open", self)
        loadDiaAction.triggered.connect(self.loadDia)

        # exportTrnsysAction = QAction(QIcon('images/font-file.png'), "Export trnsys file", self)
        # exportTrnsysAction.triggered.connect(self.exportTrnsys)

        updateConfigAction = QAction(QIcon('images/updateConfig.png'), "Update run.config", self)
        updateConfigAction.triggered.connect(self.updateRun)

        runSimulationAction = QAction(QIcon('images/runSimulation.png'), "Run simulation", self)
        runSimulationAction.triggered.connect(self.runSimulation)

        processSimulationAction = QAction(QIcon('images/processSimulation.png'), "Process data", self)
        processSimulationAction.triggered.connect(self.processSimulation)

        # renameDiaAction = QAction(QIcon('images/text-label.png'), "Rename system diagram", self)
        # renameDiaAction.triggered.connect(self.renameDia)

        deleteDiaAction = QAction(QIcon('images/trash.png'), "Delete diagram", self)
        deleteDiaAction.triggered.connect(self.deleteDia)

        # groupNewAction = QAction(QIcon('images/add-square.png'), "Create Group", self)
        # groupNewAction.triggered.connect(self.createGroup)

        # autoArrangeAction = QAction(QIcon('images/site-map.png'), "Tidy up connections", self)
        # autoArrangeAction.triggered.connect(self.tidyUp)

        zoomInAction = QAction(QIcon('images/zoom-in.png'), "Zoom in", self)
        zoomInAction.triggered.connect(self.setZoomIn)

        zoomOutAction = QAction(QIcon('images/zoom-Out.png'), "Zoom out", self)
        zoomOutAction.triggered.connect(self.setZoomOut)

        # zoom0Action = QAction(QIcon('images/zoom-0.png'), "Reset zoom", self)
        # zoom0Action.triggered.connect(self.setZoom0)

        # copyAction = QAction(QIcon('images/clipboard.png'), "Copy to clipboard", self)
        # copyAction.triggered.connect(self.copySelection)
        # copyAction.setShortcut("Ctrl+c")

        # pasteAction = QAction(QIcon('images/puzzle-piece.png'), "Paste from clipboard", self)
        # pasteAction.triggered.connect(self.pasteSelection)
        # pasteAction.setShortcut("Ctrl+v")

        toggleConnLabels = QAction(QIcon('images/labelToggle.png'), "Toggle labels", self)
        toggleConnLabels.triggered.connect(self.toggleConnLabels)

        exportHydraulicsAction = QAction(QIcon('images/exportHydraulics.png'), "Export hydraulic.ddck", self)
        exportHydraulicsAction.triggered.connect(self.exportHydraulicsDdck)

        exportHydCtrlAction = QAction(QIcon('images/exportHydraulicControl.png'), "Export hydraulic_control.ddck", self)
        exportHydCtrlAction.triggered.connect(self.exportHydraulicControl)

        exportDckAction = QAction(QIcon('images/exportDck.png'), "Export dck", self)
        exportDckAction.triggered.connect(self.exportDck)

        editGroupsAction = QAction(QIcon('images/modal-list.png'), "Edit groups/loops", self)
        editGroupsAction.triggered.connect(self.editGroups)

        selectMultipleAction = QAction(QIcon('images/elastic.png'), "Select multiple items", self)
        selectMultipleAction.triggered.connect(self.createSelection)
        selectMultipleAction.setShortcut("s")

        # deleteShortcut = QtGui.QKeySequence("Delete, Backspace, Ctrl+d")
        # multipleDeleteAction = QAction("Delete selection", self)
        # multipleDeleteAction.triggered.connect(self.deleteMultiple)
        # multipleDeleteAction.setShortcuts(deleteShortcut)

        # toggleEditorModeAction = QAction("Toggle editor mode", self)
        # toggleEditorModeAction.triggered.connect(self.toggleEditorMode)
        # toggleEditorModeAction.setShortcut("m")

        toggleSnapAction = QAction("Toggle snap grid", self)
        toggleSnapAction.triggered.connect(self.toggleSnap)
        toggleSnapAction.setShortcut("a")

        toggleAlignModeAction = QAction("Toggle align mode", self)
        toggleAlignModeAction.triggered.connect(self.toggleAlignMode)
        toggleAlignModeAction.setShortcut("q")

        runMassflowSolverAction = QAction(QIcon('images/runMfs.png'), "Run the massflow solver", self)
        runMassflowSolverAction.triggered.connect(self.runAndVisMf)

        openVisualizerAction = QAction(QIcon('images/visMfs.png'), "Start visualization of mass flows", self)
        openVisualizerAction.triggered.connect(self.visualizeMf)

        # runMassflowSolverAction = QAction(QIcon('images/gear.png'), "Run the massflow solver", self)
        # runMassflowSolverAction.triggered.connect(self.runMassflowSolver)

        trnsysList = QAction(QIcon('images/bug-1.png'), "Print trnsysObj", self)
        trnsysList.triggered.connect(self.mb_debug)

        loadVisual = QAction(QIcon('images/hard-drive.png'), "Load MRF", self)
        loadVisual.triggered.connect(self.loadVisualization)

        # testAppAction = QAction("Test", self)
        # testAppAction.triggered.connect(self.testApp)
        # testAppAction.setShortcut("Ctrl+t")

        runAction = QAction(QIcon('images/rotate-to-right.png'), "Run", self)
        runAction.triggered.connect(self.runApp)

        # Tool bar
        tb = self.addToolBar('Main Toolbar...')
        tb.setObjectName('Toolbar')
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
        # tb.addAction(exportTrnsysAction)
        # tb.addAction(renameDiaAction)
        # tb.addAction(groupNewAction)
        # tb.addAction(autoArrangeAction)
        # tb.addAction(zoom0Action)
        # tb.addAction(copyAction)
        # tb.addAction(pasteAction)
        # tb.addAction(editGroupsAction)
        # tb.addAction(selectMultipleAction)
        # tb.addAction(runMassflowSolverAction)
        # tb.addAction(loadVisual)
        # tb.addAction(trnsysList)
        # tb.addAction(runAction)
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

        # fileMenuSaveAsAction = QAction("Save as", self)
        # fileMenuSaveAsAction.triggered.connect(self.saveDiaAs)
        # self.fileMenu.addAction(fileMenuSaveAsAction)

        # changeSettingsAction = QAction("Change settings", self)
        # changeSettingsAction.triggered.connect(self.changeSettings)
        # self.fileMenu.addAction(changeSettingsAction)

        exportAsPDF = QAction("Export as PDF", self)
        exportAsPDF.triggered.connect(self.exportPDF)
        exportAsPDF.setShortcut("Ctrl+e")
        self.fileMenu.addAction(exportAsPDF)

        # exportAsEMF = QAction("Export as EMF", self)
        # exportAsEMF.triggered.connect(self.exportEMF)
        # exportAsEMF.setShortcut("Ctrl+F")
        # self.fileMenu.addAction(exportAsEMF)

        # movePortAction = QAction("Move direct ports", self)
        # movePortAction.triggered.connect(self.movePorts)
        # movePortAction.setShortcut("ctrl+m")

        # setPathAction = QAction("Set Paths", self)
        # setPathAction.triggered.connect(self.setPaths)
        # self.fileMenu.addAction(setPathAction)

        debugConnections = QAction("Debug Conn", self)
        debugConnections.triggered.connect(self.debugConns)
        self.fileMenu.addAction(debugConnections)

        self.editMenu = QMenu("Edit")
        # self.editMenu.addAction(toggleEditorModeAction)
        # self.editMenu.addAction(multipleDeleteAction)
        self.editMenu.addAction(toggleSnapAction)
        self.editMenu.addAction(toggleAlignModeAction)
        # self.editMenu.addAction(movePortAction)
        # self.editMenu.addAction(copyAction)
        # self.editMenu.addAction(pasteAction)
        # self.editMenu.addAction(testAppAction)

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

        # self.undowidget = QUndoView(self.undoStack, self)
        # self.undowidget.setMinimumSize(300, 100)

    def changeSettings(self):
        settingsDialog = settingsDlg(self)

        if ret == 1:
            self.projectFolder, projectFile = os.path.split(
                QFileDialog.getOpenFileName(self, "Open diagram", filter="*.json")[0].replace('/', '\\'))

    def loadDialogue(self):
        self.projectFolder, projectFile = os.path.split(
            QFileDialog.getOpenFileName(self, "Open diagram", filter="*.json")[0].replace('/', '\\'))

        if projectFile != '':
            properProjectCheck1 = os.path.split(self.projectFolder)[-1] == projectFile.replace('.json', '')
            properProjectCheck2 = 'ddck' in os.listdir(self.projectFolder)
            if properProjectCheck1 and properProjectCheck2:
                self.loadValue = 'load'
            else:
                projectMB = QMessageBox(self)
                projectMB.setText(
                    "The json you are opening does not have a proper project folder environment. "
                    "Do you want to continue and create one?")
                projectMB.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
                projectMB.setDefaultButton(QMessageBox.Cancel)
                projectRet = projectMB.exec()

                if projectRet == QMessageBox.Cancel:
                    self.loadValue = 'cancel'
                else:
                    self.loadValue = 'json'
                    self.jsonPath = os.path.join(self.projectFolder, projectFile)
            return False
        else:
            self.logger.info('Aborted opening another project')
            return True

    def newDia(self):
        qmb = QMessageBox()
        qmb.setText("Are you sure you want to start a new project? Unsaved progress on the current one will be lost.")
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == QMessageBox.Yes:
            self.logger.info("Initializing new project")

            self.loadValue = 'new'
            pathDialog = FolderSetUp(self)
            self.projectFolder = pathDialog.projectFolder

            self.centralWidget = self._createDiagramEditor()
            self.setCentralWidget(self.centralWidget)
        else:
            self.logger.info("Canceling")
            return

    def saveDia(self):
        self.logger.info("Saving diagram")
        self.centralWidget.save()

    def copyToNew(self):
        self.logger.info("Copying project to new folder")

        self.loadValue = 'copy'
        pathDialog = FolderSetUp(self)
        self.projectFolder = pathDialog.projectFolder

        shutil.copytree(self.centralWidget.projectFolder, self.projectFolder)

        jsonOld = os.path.split(self.centralWidget.projectFolder)[-1] + '.json'
        self.centralWidget.projectFolder = self.projectFolder
        jsonNew = os.path.split(self.projectFolder)[-1] + '.json'
        os.rename(os.path.join(self.projectFolder, jsonOld), os.path.join(self.projectFolder, jsonNew))

        jsonPath = os.path.join(self.projectFolder, jsonNew)

        self.centralWidget = self._createDiagramEditor()
        self.setCentralWidget(self.centralWidget)
        self.centralWidget.save(showWarning=False)

    def saveDiaAs(self):
        self.logger.info("Saving diagram as...")
        self.centralWidget.saveAs()

    def loadDia(self):
        self.logger.info("Loading diagram")
        self.openFile()

    def updateRun(self):
        self.logger.info("Updating run.config")
        configPath = os.path.join(self.projectFolder, 'run.config')
        runConfig = configFile(configPath, self.centralWidget)
        runConfig.updateConfig()

    def runSimulation(self):
        ddckPath = os.path.join(self.projectFolder, "ddck")

        #   Check hydraulic.ddck
        hydraulicPath = os.path.join(ddckPath, "hydraulic\\hydraulic.ddck")
        if not os.path.isfile(hydraulicPath):
            self.exportHydraulicsDdck()
        infile = open(hydraulicPath, 'r')
        hydraulicLines = infile.readlines()
        blackBoxLines = []
        for i in range(len(hydraulicLines)):
            if "Black box component temperatures" in hydraulicLines[i]:
                j = i + 1
                while hydraulicLines[j] != '\n':
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
                "Please make sure the black box component temperatures are correct in hydraulic.ddck before starting a simluation.")
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return

        #   Check ddcks of storage tanks
        storageWithoutFile = []
        for object in self.centralWidget.trnsysObj:
            if isinstance(object, StorageTank):
                storageTankFile = os.path.join(object.displayName, object.displayName + ".ddck")
                storageTankPath = os.path.join(ddckPath, storageTankFile)
                if not (os.path.isfile(storageTankPath)):
                    storageWithoutFile.append(object.displayName + "\n")

        if not (not (storageWithoutFile)):
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
        executionFailed, errorStatement = runApp.runAction(self.logger, self.centralWidget.projectFolder)

        if executionFailed:
            messageText = "Exception while trying to execute RunParallelTrnsys:\n\n" + errorStatement
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
        executionFailed, errorStatement = processApp.processAction(self.logger, self.centralWidget.projectFolder)

        if executionFailed:
            messageText = "Exception while trying to execute RunParallelTrnsys:\n\n" + errorStatement
            qmb = QMessageBox()
            qmb.setText(messageText)
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()

        return

    def exportTrnsys(self):
        self.logger.info("Exporting Trnsys file...")
        noErrorExists = self.debugConns()
        qmb = QMessageBox()

        ddckFolder = os.path.join(self.projectFolder, 'ddck')
        ddckFolders = os.listdir(ddckFolder)
        numberOfControlFolders = 0

        for folder in ddckFolders:
            if 'Control' in folder:
                controlFolder = os.path.join(ddckFolder, folder)
                numberOfControlFolders += 1

        controlMissing = True

        if numberOfControlFolders > 1:
            qmb.setText("A system can only have one control!")
            qmb.exec_()
            return
        elif numberOfControlFolders == 1:
            for file in os.listdir(controlFolder):
                if file.endswith('.ddck'):
                    controlMissing = False

        if controlMissing:
            qmb.setText("Please add a control-ddck before exporting!")
            qmb.exec_()
            return

        # if self.centralWidget.controlExists < 1:

        if not noErrorExists:
            qmb.setText("Ignore connection errors and continue with export?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                self.logger.info("Overwriting")
                # continue
            else:
                self.logger.info("Canceling")
                return
        self.centralWidget.exportData()

    def renameDia(self):
        self.logger.info("Renaming diagram...")
        # self.centralWidget.propertiesDlg()
        self.centralWidget.showDiagramDlg()

    def deleteDia(self):
        qmb = QMessageBox()
        qmb.setText("Are you sure you want to delete the diagram? (There is no possibility to \"undo\".)")
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
        mfrFile, tempFile = self.runMassflowSolver()
        if os.path.isfile(mfrFile) and os.path.isfile(tempFile):
            MassFlowVisualizer(self, mfrFile, tempFile)
            self.massFlowEnabled = True
        else:
            self.logger.info("No mfrFile or tempFile found!")

    def visualizeMf(self):
        qmb = QMessageBox()
        qmb.setText("Please select the mass flow rate prt-file that you want to visualize.")
        qmb.setStandardButtons(QMessageBox.Ok)
        qmb.setDefaultButton(QMessageBox.Ok)
        qmb.exec()

        mfrFile = QFileDialog.getOpenFileName(self, "Open diagram", filter="*Mfr.prt")[0].replace('/', '\\')
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
        qmb.setText("Are you sure you want to open another project? Unsaved progress on the current one will be lost.")
        qmb.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()

        if ret == QMessageBox.Yes:
            loadingAborted = self.loadDialogue()
            if loadingAborted:
                return
            self.centralWidget.idGen.reset()
            self.centralWidget.delBlocks()

            if self.loadValue == 'json':
                pathDialog = FolderSetUp(self)
                self.projectFolder = pathDialog.projectFolder

            self.centralWidget = self._createDiagramEditor()
            self.setCentralWidget(self.centralWidget)

            if self.loadValue == 'json':
                self.centralWidget.save()

            try:
                self.exportedTo
            except AttributeError:
                pass
            else:
                del self.exportedTo
        else:
            return

    def openFileAtStartUp(self):
        """
        Opens the most recently modified file from the recent folder

        Things to note : file directory must be changed to corresponding directory on individual PCs
        -------
        """

        self.logger.info("Opening diagram")
        self.centralWidget.delBlocks()

        # list_of_files = glob.glob('U:/Desktop/TrnsysGUI/trnsysGUI/recent/*')

        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        filePath = os.path.join(ROOT_DIR, 'recent')
        filePath = os.path.join(filePath, '*')
        list_of_files = glob.glob(filePath)

        if len(list_of_files) != 0:
            latest_file = max(list_of_files, key=os.path.getmtime)
        else:
            latest_file = ''

        while len(list_of_files) > 10:
            list_of_files = glob.glob(filePath)
            try:
                fileToDelete = min(list_of_files, key=os.path.getmtime)
            except FileNotFoundError:
                self.logger.info("File not found")
            else:
                os.remove(fileToDelete)

        try:
            latest_file
        except FileNotFoundError:
            self.logger.info("File not found")
        else:
            if latest_file != '':
                self.currentFile = latest_file
                self.centralWidget.delBlocks()
                self.centralWidget.decodeDiagram(latest_file)
            else:
                self.logger.info("No filename available")

    def toggleConnLabels(self):
        self.labelVisState = not self.labelVisState
        self.centralWidget.setConnLabelVis(self.labelVisState)

    def exportHydraulicsDdck(self):
        statusQuo = self.labelVisState
        if not statusQuo:
            self.toggleConnLabels()
        self.centralWidget.exportData(exportTo='ddck')
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

        exportPath = self.centralWidget.exportData(exportTo='mfs')
        self.exportedTo = exportPath
        self.logger.info(exportPath)
        if exportPath != 'None':
            msgb = QMessageBox(self)
            if not os.path.isfile(self.centralWidget.trnsysPath):
                msgb.setText("TRNExe.exe not found!")
                msgb.exec()
                return 0, 0
            self.logger.info("trnsyspath: " + self.centralWidget.trnsysPath)
            cmd = self.centralWidget.trnsysPath + ' ' + str(exportPath) + r' /H'
            os.system(cmd)
            mfrFile = os.path.join(self.projectFolder, self.projectFolder.split("\\")[-1] + '_Mfr.prt')
            tempFile = os.path.join(self.projectFolder, self.projectFolder.split("\\")[-1] + '_T.prt')
            if not os.path.isfile(mfrFile) or not os.path.isfile(tempFile):
                msgb.setText("Execution of Trnsys NOT succesful")
                msgb.exec()
                del self.exportedTo
            else:
                if not self.calledByVisualizeMf:
                    msgb.setText("Execution of Trnsys succesful")
                    msgb.exec()
            self.calledByVisualizeMf = False
            return mfrFile, tempFile

    # def loadVisualization(self):
    #
    #     currentFilePath = self.currentFile
    #     if '\\' in currentFilePath:
    #         diaName = currentFilePath.split('\\')[-1][:-5]
    #     elif '/' in currentFilePath:
    #         diaName = currentFilePath.split('/')[-1][:-5]
    #     else:
    #         diaName = currentFilePath
    #     if getattr(sys, 'frozen', False):
    #         ROOT_DIR = os.path.dirname(sys.executable)
    #     elif __file__:
    #         ROOT_DIR = os.path.dirname(__file__)
    #
    #     filepaths = os.path.join(ROOT_DIR, 'filepaths')
    #     with open(filepaths, 'r') as file:
    #         data = file.readlines()
    #
    #     filePath = data[0][:-1]
    #     MfrFilePath = os.path.join(filePath, diaName + '_Mfr.prt')
    #     TempFilePath = os.path.join(filePath, diaName + '_T.prt')
    #     print(MfrFilePath, TempFilePath)
    #
    #     if os.path.exists(MfrFilePath) and os.path.exists(TempFilePath):
    #         MassFlowVisualizer(self, MfrFilePath, TempFilePath)
    #         self.massFlowEnabled = True
    #     else:
    #         msgb = QMessageBox(self)
    #         msgb.setText("MFR or Temperature file does not exist!")
    #         msgb.exec()

    def loadVisualization(self):
        MfrFile = QFileDialog.getOpenFileName(self, "Select Mfr File", "exports", filter="*_Mfr.prt")[0]
        if MfrFile == '':
            msgb = QMessageBox(self)
            msgb.setText("No Mfr file chosen!")
            msgb.exec()
            return
        TempFile = QFileDialog.getOpenFileName(self, "Select Temperature File", "exports", filter="*_T.prt")[0]
        if TempFile == '':
            msgb = QMessageBox(self)
            msgb.setText("No Temperature file chosen!")
            msgb.exec()
            return

        selectedMfrFileName = str(MfrFile).split("/")[-1][:-8]
        selectedTempFileName = str(TempFile).split("/")[-1][:-6]

        currentFilePath = self.currentFile
        if '\\' in currentFilePath:
            diaName = currentFilePath.split('\\')[-1][:-5]
        elif '/' in currentFilePath:
            diaName = currentFilePath.split('/')[-1][:-5]
        else:
            diaName = currentFilePath

        if selectedMfrFileName == selectedTempFileName == diaName:
            MassFlowVisualizer(self, MfrFile, TempFile)
            self.massFlowEnabled = True
        else:
            self.logger.info(selectedMfrFileName, selectedTempFileName, diaName)
            msgb = QMessageBox(self)
            msgb.setText("MFR or Temperature file does not correspond to current diagram!")
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
        msgb.setText("Currrent version is " + __version__ + " with status " + __status__)
        msgb.exec()

    def showCredits(self):
        msgb = QMessageBox(self)
        msgb.setText("<p><b>Contributors:</b></p>"
                     "<p>Stefano Marti, Dani Carbonell, Mattia Battaglia, Jeremias Schmidli, and Martin Neugebauer.")
        # "Icons made by Jeremias Schmidli and with icons by Vaadin from  www.flaticon.com</p>"
        msgb.exec()

    def testApp(self):
        self.newDia()
        self.centralWidget.testFunction()
        self.newDia()

        msgb = QMessageBox(self)
        msgb.setText("Test Complete, please restart the application. ")
        msgb.exec()

        self.close()

    def exportPDF(self):
        self.centralWidget.printPDF()

    def closeEvent(self, e):
        qmb = QMessageBox()
        qmb.setText("Do you want to save the current state of the project before closing the program?")
        qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()
        if ret == QMessageBox.Cancel:
            e.ignore()
        elif ret == QMessageBox.Close:
            e.accept()
        elif ret == QMessageBox.Save:
            self.centralWidget.save()
            e.accept

    def setPaths(self):
        """
        Sets the export, diagram, ddck and trnsys path.
        """
        pathDialog = PathSetUp(self)

    def setFolder(self):
        """
            Sets the export, diagram, ddck and trnsys path.
        """
        pathDialog = FolderSetUp(self)

    def checkFilePaths(self):
        """
        Checks if all file paths have been set. If not, call setPaths
        """
        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        filepath = os.path.join(ROOT_DIR, 'filepaths.txt')
        if not os.path.isfile(filepath):
            open(filepath, 'w+')
            open(filepath, 'w+')
        with open(filepath, 'r') as file:
            data = file.readlines()
        if len(data) < 2:
            pathSetUpDialog = PathSetUp(self)

    def setTrnsysPath(self):
        """
        Sets the trnsys path during start up, after user has defined it.
        """
        noOfRequiredPaths = 4
        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        filepaths = os.path.join(ROOT_DIR, 'filepaths.txt')
        with open(filepaths, 'r') as file:
            data = file.readlines()
        if len(data) == noOfRequiredPaths:
            self.centralWidget.trnsysPath = os.path.join(data[3][:-1], 'TRNExe.exe')

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
                    msgBox.setText("both %s and %s are input ports into %s" % (connName1, connName2, objName))
                    msgBox.exec_()
                    self.noErrorConns = False

                elif objInput == connToInputFromPort and objOutput == connToOutputFromPort:
                    msgBox = QMessageBox()
                    msgBox.setText("both %s and %s are output ports from %s" % (connName1, connName2, objName))
                    msgBox.exec_()
                    self.noErrorConns = False
        return self.noErrorConns

    def runApp(self):
        runApp = RunMain()
        if self.centralWidget.projectPath == '':
            self.logger.info("Temp path:", self.centralWidget.projectFolder)
            runApp.runAction(self.centralWidget.projectFolder)
        else:
            self.logger.info("Project path:", self.centralWidget.projectPath)
            runApp.runAction(self.centralWidget.projectPath)

    def _createDiagramEditor(self):
        return _de.Editor(self, self.projectFolder, self.jsonPath, self.loadValue, self.logger)


def main():
    global logger
    arguments = args.getArgsOrExit()

    logger = log.setup_custom_logger('root', arguments.logLevel)
    app = QApplication(sys.argv)
    app.setApplicationName("Diagram Creator")
    form = MainWindow(logger)
    form.showMaximized()
    form.show()
    form.checkFilePaths()
    form.setTrnsysPath()

    tracer = trc.createTracer(arguments.shallTrace)
    tracer.run(lambda: app.exec())


if __name__ == '__main__':
    main()

# Found bug: when dragging bridging connection over another segment, crash
# Found glitch: when having a disr segment, gradient is not correct anymore
# Found bug: IceStorage, when creating new connection and moving block, the connection does not update position
# Found bug: When in mode 1, sometimes dragging leads to segments collaps to a small point

# Improve autoarrange of connections
# TODO:   old/Prevent loops when adding connections to StorageBlock
# TODO 7: Solve mix up between i/o and left/right side

# There is a mess introduced with kwargs because the dencoder returns objects, which cannot have any
# connection to the "outside" of the decoder. This could maybe be improved by returning just the dict
# to the DiagramEditor class, which then can easily create the objects correctly.
