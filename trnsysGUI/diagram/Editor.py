# pylint: skip-file
# type: ignore

import json
import os
import pathlib as _pl
import pkgutil as _pu
import shutil
import sys

import pandas as pd
from PyQt5 import QtGui
from PyQt5.QtCore import QSize, Qt, QLineF, QCoreApplication, QFileInfo, QDir
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtSvg import QSvgGenerator
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QListView,
    QVBoxLayout,
    QListWidget,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSplitter,
    QGraphicsItemGroup,
    QGraphicsLineItem,
    QMessageBox,
    QFileDialog,
    QTreeView,
    QPushButton,
)

import trnsysGUI.images as _img
from trnsysGUI.BlockDlg import BlockDlg
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.ConfigureStorageDialog import ConfigureStorageDialog
from trnsysGUI.Connection import Connection
from trnsysGUI.Connector import Connector
from trnsysGUI.CreateConnectionCommand import CreateConnectionCommand
from trnsysGUI.DifferenceDlg import DifferenceDlg
from trnsysGUI.Export import Export
from trnsysGUI.FileOrderingDialog import FileOrderingDialog
from trnsysGUI.GenericPortPairDlg import GenericPortPairDlg
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.Group import Group
from trnsysGUI.GroupChooserBlockDlg import GroupChooserBlockDlg
from trnsysGUI.GroupChooserConnDlg import GroupChooserConnDlg
from trnsysGUI.IdGenerator import IdGenerator
from trnsysGUI.LibraryModel import LibraryModel
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PipeDataHandler import PipeDataHandler
from trnsysGUI.PortItem import PortItem
from trnsysGUI.PumpDlg import PumpDlg
from trnsysGUI.StorageTank import StorageTank
from trnsysGUI.TVentil import TVentil
from trnsysGUI.TVentilDlg import TVentilDlg
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.TestDlg import TestDlg
from trnsysGUI.Test_Export import Test_Export
from trnsysGUI.copyGroup import copyGroup
from trnsysGUI.diagram.Decoder import Decoder
from trnsysGUI.diagram.DecoderPaste import DecoderPaste
from trnsysGUI.diagram.Encoder import Encoder
from trnsysGUI.diagram.Scene import Scene
from trnsysGUI.diagram.View import View
from trnsysGUI.diagramDlg import diagramDlg
from trnsysGUI.groupDlg import groupDlg
from trnsysGUI.groupsEditor import groupsEditor
from trnsysGUI.hxDlg import hxDlg
from trnsysGUI.newDiagramDlg import newDiagramDlg
from trnsysGUI.segmentDlg import segmentDlg
import trnsysGUI as _tgui


class Editor(QWidget):
    """
    This class is the central widget of the MainWindow.
    It contains the items library, diagram graphics scene and graphics view, and the inspector widget

    Function of Connections:
    Logically:
    A Connection is composed of a fromPort and a toPort, which gives the direction of the pipe.
    Ports are attached to Blocks.
    Initially, there is a temporary fromPort set to None.
    As soon any Port is clicked and dragged, tempStartPort is set to that Port and startedConnectino is set to True.
    -> startConnection()
    If the mouse is then released over a different Port, a Connection is created, otherwise startedConnection is set to False
    and the process is interrupted.
    -> createConnection()
    Visually:
    A diagram editor has a QGraphicsLineItem (connLineItem) which is set Visible only when a connection is being created

    Function of BlockItems:
    Items can be added to the library by adding them to the model of the library broswer view.
    Then they can be dragged and dropped into the diagram view.

    Function of trnsysExport:
    When exporting the trnsys file, exportData() is called.

    Function of save and load:
    A diagram can be saved to a json file by calling encodeDiagram and can then be loaded by calling decodeDiagram wiht
    appropiate filenames.

    Function of copy-paste:
    Copying a rectangular part of the diagram to the clipboard is just encoding the diagram to the file clipboard.json,
    and pasting will load the clipboard using a slighly different decoder than for loading an entire diagram.
    When the elements are pasted, they compose a group which can be dragged around and is desintegrated when the mouse
    is released.
    It is controlled by the attributes selectionMode, groupMode, copyMode and multipleSelectedMode

    Attributes
    ----------
    projectFolder : str
        Path to the folder of the project
    diagramName : str
        Name used for saving the diagram
    saveAsPath : :obj:`Path`
        Default saving location is trnsysGUI/diagrams, path only set if "save as" used
    idGen : :obj:`IdGenerator`
        Is used to distribute ids (id, trnsysId(for trnsysExport), etc)
    selectionMode : bool
        Enables/disables selection rectangle in Scene
    groupMode : bool
        Enables creation of a new group in Scene
    copyMode : bool
        Enables copying elements in the selection rectangle
    multipleSelectedMode : bool
        Unused
    alignMode : bool
        Enables mode in which a dragged block is aligned to y or x value of another one
        Toggled in the MainWindow class in toggleAlignMode()
    pasting : bool
        Used to allow dragging of the copygroup right after pasting. Set to true after decodingPaste is called.
        Set to false as soon as releasedMouse after decodePaste.
    itemsSelected : bool

    editorMode : int
        Mode 0: Pipes are PolySun-like
        Mode 1: Pipes have only 90deg angles, visio-like
    snapGrid : bool
        Enable/Disable align grid
    snapSize : int
        Size of align grid

    horizontalLayout : :obj:`QHBoxLayout`
    Contains the diagram editor and the layout containing the library browser view and the listview
    vertL : :obj:`QVBoxLayout`
    Cointains the library browser view and the listWidget

    datagen : :obj:`PipeDataHandler`
        Used for generating random massflows for every timestep to test the massflow
        visualizer prototype
    moveDirectPorts: bool
        Enables/Disables moving direct ports of storagetank (doesn't work with HxPorts yet)
    diagramScene : :obj:`QGraphicsScene`
        Contains the "logical" part of the diagram
    diagramView : :obj:`QGraphicsView`
        Contains the visualization of the diagramScene
    startedConnection : Bool
    tempStartPort : :obj:`PortItem`
    connectionList : :obj:`List` of :obj:`Connection`
    trnsysObj : :obj:`List` of :obj:`BlockItem` and :obj:`Connection`
    groupList : :obj:`List` of :obj:`BlockItem` and :obj:`Connection`
    graphicalObj : :obj:`List` of :obj:`GraphicalItem`
    connLine : :obj:`QLineF`
    connLineItem = :obj:`QGraphicsLineItem`

    """

    def __init__(self, parent, projectFolder, jsonPath, loadValue, logger):
        QWidget.__init__(self, parent)

        self.logger = logger

        self.logger.info("Initializing the diagram editor")

        self.projectFolder = projectFolder

        self.diagramName = os.path.split(self.projectFolder)[-1] + ".json"
        self.saveAsPath = _pl.Path()
        self.idGen = IdGenerator()

        # Generator for massflow display testing
        self.datagen = PipeDataHandler(self)

        self.testEnabled = False
        self.existReference = True

        self.controlExists = 0
        self.controlDirectory = ""

        self.selectionMode = False
        self.groupMode = False
        self.copyMode = False
        self.multipleSelectedMode = False

        self.alignMode = False

        self.pasting = False
        self.itemsSelected = False

        self.moveDirectPorts = False

        self.editorMode = 1

        # Related to the grid blocks can snap to
        self.snapGrid = False
        self.snapSize = 20

        self.trnsysPath = _pl.Path(r"C:\Trnsys17\Exe\TRNExe.exe")

        self.horizontalLayout = QHBoxLayout(self)
        self.libraryBrowserView = QListView(self)
        self.libraryModel = LibraryModel(self)

        self.libraryBrowserView.setGridSize(QSize(65, 65))
        self.libraryBrowserView.setResizeMode(QListView.Adjust)
        self.libraryModel.setColumnCount(0)

        componentNamesWithIcon = [
            ("Connector", _img.CONNECTOR_SVG.icon()),
            ("TeePiece", _img.TEE_PIECE_SVG.icon()),
            ("TVentil", _img.T_VENTIL_SVG.icon()),
            ("WTap_main", _img.W_TAP_MAIN_SVG.icon()),
            ("WTap", _img.W_TAP_SVG.icon()),
            ("Pump", _img.PUMP_SVG.icon()),
            ("Collector", _img.COLLECTOR_SVG.icon()),
            ("GroundSourceHx", _img.GROUND_SOURCE_HX_SVG.icon()),
            ("PV", _img.PV_SVG.icon()),
            ("HP", _img.HP_SVG.icon()),
            ("HPTwoHx", _img.HP_TWO_HX_SVG.icon()),
            ("HPDoubleDual", _img.HP_DOUBLE_DUAL_SVG.icon()),
            ("AirSourceHP", _img.AIR_SOURCE_HP_SVG.icon()),
            ("StorageTank", _img.STORAGE_TANK_SVG.icon()),
            ("IceStorage", _img.ICE_STORAGE_SVG.icon()),
            ("PitStorage", _img.PIT_STORAGE_SVG.icon()),
            ("IceStorageTwoHx", _img.ICE_STORAGE_TWO_HX_SVG.icon()),
            ("ExternalHx", _img.EXTERNAL_HX_SVG.icon()),
            ("Radiator", _img.RADIATOR_SVG.icon()),
            ("Boiler", _img.BOILER_SVG.icon()),
            ("GenericBlock", _img.GENERIC_BLOCK_PNG.icon()),
            ("GraphicalItem", _img.GENERIC_ITEM_PNG.icon())
        ]

        libItems = [QtGui.QStandardItem(icon, name) for name, icon in componentNamesWithIcon]

        for i in libItems:
            self.libraryModel.appendRow(i)

        self.libraryBrowserView.setModel(self.libraryModel)
        self.libraryBrowserView.setViewMode(self.libraryBrowserView.IconMode)
        self.libraryBrowserView.setDragDropMode(self.libraryBrowserView.DragOnly)

        self.diagramScene = Scene(self)
        self.diagramView = View(self.diagramScene, self)

        # For list view
        self.vertL = QVBoxLayout()
        self.vertL.addWidget(self.libraryBrowserView)
        self.vertL.setStretchFactor(self.libraryBrowserView, 2)
        self.listV = QListWidget()
        self.vertL.addWidget(self.listV)
        self.vertL.setStretchFactor(self.listV, 1)

        # for file browser
        self.projectPath = ""  # XXX
        self.fileList = []  # XXX

        if loadValue == "new" or loadValue == "json":
            self.createProjectFolder()

        self.fileBrowserLayout = QVBoxLayout()
        self.pathLayout = QHBoxLayout()
        self.projectPathLabel = QLabel("Project Path:")
        self.PPL = QLineEdit(self.projectFolder)
        self.PPL.setDisabled(True)

        # self.setProjectPathButton = QPushButton("Change path")
        # self.setProjectPathButton.clicked.connect(self.setProjectPath)
        # self.openProjectButton = QPushButton("Open Project")
        # self.openProjectButton.clicked.connect(self.openProject)

        self.pathLayout.addWidget(self.projectPathLabel)
        self.pathLayout.addWidget(self.PPL)
        # self.pathLayout.addWidget(self.setProjectPathButton)
        # self.pathLayout.addWidget(self.openProjectButton)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.splitter = QSplitter(
            Qt.Vertical,
        )
        self.splitter.setChildrenCollapsible(False)
        self.scroll.setWidget(self.splitter)
        self.scroll.setFixedWidth(350)
        self.fileBrowserLayout.addLayout(self.pathLayout)
        self.fileBrowserLayout.addWidget(self.scroll)
        self.createDdckTree(self.projectFolder)

        if loadValue == "new" or loadValue == "json":
            self.createConfigBrowser(self.projectFolder)
            self.copyGenericFolder(self.projectFolder)
            self.createHydraulicDir(self.projectFolder)
            self.createWeatherAndControlDirs(self.projectFolder)

        self.horizontalLayout.addLayout(self.vertL)
        self.horizontalLayout.addWidget(self.diagramView)
        self.horizontalLayout.addLayout(self.fileBrowserLayout)
        self.horizontalLayout.setStretchFactor(self.diagramView, 5)
        self.horizontalLayout.setStretchFactor(self.libraryBrowserView, 1)

        self.startedConnection = False
        self.tempStartPort = None
        self.connectionList = []
        self.trnsysObj = []
        self.groupList = []
        self.graphicalObj = []

        self.defaultGroup = Group(0, 0, 100, 100, self.diagramScene)
        self.defaultGroup.setName("defaultGroup")

        self.copyGroupList = QGraphicsItemGroup()
        self.selectionGroupList = QGraphicsItemGroup()

        self.printerUnitnr = 0

        # For debug button
        # a = 400  # Start of upmost button y-value
        # b = 50  # distance between starts of button y-values
        # b_start = 75

        # self.button = QPushButton(self)
        # self.button.setText("Print info")
        # self.button.move(b_start, a)
        # self.button.setMinimumSize(120, 40)
        # self.button.clicked.connect(self.button1_clicked)

        # Different colors for connLineColor
        colorsc = "red"
        linePx = 4
        if colorsc == "red":
            connLinecolor = QColor(Qt.red)
            # connLinecolor = QColor(252, 60, 60)
        elif colorsc == "blueish":
            connLinecolor = QColor(3, 124, 193)  # Blue
        elif colorsc == "darkgray":
            connLinecolor = QColor(140, 140, 140)  # Gray
        else:
            connLinecolor = QColor(196, 196, 196)  # Gray

        # Only for displaying on-going creation of connection
        self.connLine = QLineF()
        self.connLineItem = QGraphicsLineItem(self.connLine)
        self.connLineItem.setPen(QtGui.QPen(connLinecolor, linePx))
        self.connLineItem.setVisible(False)
        self.diagramScene.addItem(self.connLineItem)

        # For line that shows quickly up when using the align mode
        self.alignYLine = QLineF()
        self.alignYLineItem = QGraphicsLineItem(self.alignYLine)
        self.alignYLineItem.setPen(QtGui.QPen(QColor(196, 249, 252), 2))
        self.alignYLineItem.setVisible(False)
        self.diagramScene.addItem(self.alignYLineItem)

        # For line that shows quickly up when using align mode
        self.alignXLine = QLineF()
        self.alignXLineItem = QGraphicsLineItem(self.alignXLine)
        self.alignXLineItem.setPen(QtGui.QPen(QColor(196, 249, 252), 2))
        self.alignXLineItem.setVisible(False)
        self.diagramScene.addItem(self.alignXLineItem)

        if loadValue == "load" or loadValue == "copy":
            self.decodeDiagram(os.path.join(self.projectFolder, self.diagramName), loadValue=loadValue)
        elif loadValue == "json":
            self.decodeDiagram(jsonPath, loadValue=loadValue)

    # Debug function
    def dumpInformation(self):
        self.logger.debug("Diagram information:")
        self.logger.debug("Mode is " + str(self.editorMode))

        self.logger.debug("Next ID is " + str(self.idGen.getID()))
        self.logger.debug("Next cID is " + str(self.idGen.getConnID()))

        self.logger.debug("TrnsysObjects are:")
        for t in self.trnsysObj:
            self.logger.debug(str(t))
        self.logger.debug("")

        self.logger.debug("Scene items are:")
        sItems = self.diagramScene.items()
        for it in sItems:
            self.logger.info(str(it))
        self.logger.debug("")

        for c in self.connectionList:
            c.printConn()
        self.logger.debug("")

    # Connections related methods
    def startConnection(self, port):
        """
        When a PortItem is clicked, it is saved into the tempStartPort

        Parameters
        ----------
        port : :obj:`PortItem`

        Returns
        -------

        """
        self.logger.debug("port is " + str(port))
        self.tempStartPort = port
        self.startedConnection = True

    def createConnection(self, startPort, endPort):
        """
        Creates a new connection if startPort and endPort are not the same. Is added as a command to the
        undoStack.

        Parameters
        ----------
        startPort : :obj:`PortItem`
        endPort : :obj:`PortItem`

        Returns
        -------

        """
        # print("Creating connection...")
        if startPort is not endPort:
            # if len(endPort.connectionList) == 0:
            # Connection(startPort, endPort, False, self)

            if (
                isinstance(startPort.parent, StorageTank)
                and isinstance(endPort.parent, StorageTank)
                and startPort.parent != endPort.parent
            ):
                msgSTank = QMessageBox(self)
                msgSTank.setText("Storage Tank to Storage Tank connection is not working atm!")
                msgSTank.exec_()

            command = CreateConnectionCommand(startPort, endPort, self, "CreateConn Command")
            self.parent().undoStack.push(command)

    def sceneMouseMoveEvent(self, event):
        """
        Qt method that sets the line signalling the creation of a new connection.

        Parameters
        ----------
        event

        Returns
        -------

        """
        if self.startedConnection:
            # print("Started conn, should draw")
            tempx = self.tempStartPort.scenePos().x()
            tempy = self.tempStartPort.scenePos().y()
            posx = event.scenePos().x()
            posy = event.scenePos().y()
            # print(str(posx))
            # print(str(tempx))

            self.connLineItem.setVisible(True)
            self.connLine.setLine(tempx, tempy, posx, posy)
            self.connLineItem.setLine(self.connLine)
            self.connLineItem.setVisible(True)

    def sceneMouseReleaseEvent(self, event):
        # print("Called sceneMouseReleaseEvent with startedConnection=" + str(self.startedConnection))
        if self.startedConnection:
            releasePos = event.scenePos()
            itemsAtReleasePos = self.diagramScene.items(releasePos)
            self.logger.debug("items are " + str(itemsAtReleasePos))
            for it in itemsAtReleasePos:
                if type(it) is PortItem:
                    self.createConnection(self.tempStartPort, it)
                else:
                    self.startedConnection = False
                    self.connLineItem.setVisible(False)

                    # Not necessary
                    # self.tempStartPort = None

    def cleanUpConnections(self):
        for c in self.connectionList:
            c.niceConn()
        # if self.connectionList.__len__() > 0:
        #     self.connectionList[0].clearConn()

    def exportHydraulics(self, exportTo="ddck"):
        self.logger.info("------------------------> START OF EXPORT <------------------------")

        self.sortTrnsysObj()

        fullExportText = ""

        ddckFolder = os.path.join(self.projectFolder, "ddck")

        if exportTo == "mfs":
            mfsFileName = self.diagramName.split(".")[0] + "_mfs.dck"
            exportPath = os.path.join(self.projectFolder, mfsFileName)
            if self._doesFileExistAndDontOverwrite(exportPath):
                return None

        elif exportTo == "ddck":
            hydraulicsPath = os.path.join(ddckFolder, "hydraulic\\hydraulic.ddck")

            if self._doesFileExistAndDontOverwrite(hydraulicsPath):
                return None

        self.logger.info("Printing the TRNSYS file...")

        if exportTo == "mfs":
            header = open(os.path.join(ddckFolder, "generic\\head.ddck"), "r")
            headerLines = header.readlines()
            for line in headerLines:
                if line[:4] == "STOP":
                    fullExportText += "STOP = 1 \n"
                else:
                    fullExportText += line
            header.close()
        elif exportTo == "ddck":
            fullExportText += "*************************************\n"
            fullExportText += "** BEGIN hydraulic.ddck\n"
            fullExportText += "*************************************\n\n"
            fullExportText += "*************************************\n"
            fullExportText += "** Outputs to energy balance in kWh\n"
            fullExportText += (
                "** Following this naming standard : qSysIn_name, qSysOut_name, elSysIn_name, elSysOut_name\n"
            )
            fullExportText += "*************************************\n"
            fullExportText += "EQUATIONS 1\n"
            fullExportText += "qSysOut_PipeLoss = PipeLossTot\n"

        simulationUnit = 450
        simulationType = 935
        descConnLength = 20

        exporter = Export(self.trnsysObj, self)

        blackBoxProblem, blackBoxText = exporter.exportBlackBox(exportTo=exportTo)
        if blackBoxProblem:
            return
        fullExportText += blackBoxText
        if exportTo == "mfs":
            fullExportText += exporter.exportMassFlows()
            fullExportText += exporter.exportPumpOutlets()
            fullExportText += exporter.exportDivSetting(simulationUnit - 10)

        fullExportText += exporter.exportParametersFlowSolver(
            simulationUnit, simulationType, descConnLength
        )  # , parameters, lineNrParameters)
        fullExportText += exporter.exportInputsFlowSolver()
        fullExportText += exporter.exportOutputsFlowSolver(simulationUnit)
        fullExportText += exporter.exportPipeAndTeeTypesForTemp(simulationUnit + 1)  # DC-ERROR
        fullExportText += exporter.exportPrintLoops()
        fullExportText += exporter.exportPrintPipeLoops()
        fullExportText += exporter.exportPrintPipeLosses()

        # unitnr should maybe be variable in exportData()

        fullExportText += exporter.exportMassFlowPrinter(self.printerUnitnr, 15)
        fullExportText += exporter.exportTempPrinter(self.printerUnitnr + 1, 15)

        # tes = open(os.path.join(ddckFolder, "Tes\\Tes.ddck"), "r")
        # fullExportText += tes.read()
        # tes.close()
        if exportTo == "mfs":
            fullExportText += "CONSTANTS 1\nTRoomStore=1\n"
            fullExportText += "ENDS"

        self.logger.info("------------------------> END OF EXPORT <------------------------")

        if exportTo == "mfs":
            f = open(str(exportPath), "w")
            f.truncate(0)
            f.write(fullExportText)
            f.close()
        elif exportTo == "ddck":
            if fullExportText[:1] == "\n":
                fullExportText = fullExportText[1:]
            hydraulicFolder = os.path.split(hydraulicsPath)[0]
            if not (os.path.isdir(hydraulicFolder)):
                os.makedirs(hydraulicFolder)
            f = open(str(hydraulicsPath), "w")
            f.truncate(0)
            f.write(fullExportText)
            f.close()

        self.cleanUpExportedElements()

        if exportTo == "mfs":
            return exportPath
        elif exportTo == "ddck":
            return hydraulicsPath

    def _doesFileExistAndDontOverwrite(self, folderPath):
        if not _pl.Path(folderPath).exists():
            return False

        qmb = QMessageBox(self)
        qmb.setText(f"Warning: {folderPath} already exists. Do you want to overwrite it or cancel?")
        qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
        qmb.setDefaultButton(QMessageBox.Cancel)
        ret = qmb.exec()

        if ret == QMessageBox.Cancel:
            self.canceled = True
            self.logger.info("Canceling")
            return True

        self.canceled = False
        self.logger.info("Overwriting")
        return False

    def exportHydraulicControl(self):
        self.logger.info("------------------------> START OF EXPORT <------------------------")

        self.sortTrnsysObj()

        fullExportText = ""

        ddckFolder = os.path.join(self.projectFolder, "ddck")

        hydCtrlPath = os.path.join(ddckFolder, "control\\hydraulic_control.ddck")
        if _pl.Path(hydCtrlPath).exists():
            qmb = QMessageBox(self)
            qmb.setText(
                "Warning: "
                + "The file hydraulic_control.ddck already exists in the control folder. Do you want to overwrite it or cancel?"
            )
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                self.canceled = False
                self.logger.info("Overwriting")
            else:
                self.canceled = True
                self.logger.info("Canceling")
                return

        fullExportText += "*************************************\n"
        fullExportText += "**BEGIN hydraulic_control.ddck\n"
        fullExportText += "*************************************\n"

        simulationUnit = 450
        simulationType = 935
        descConnLength = 20

        exporter = Export(self.trnsysObj, self)

        fullExportText += exporter.exportPumpOutlets()
        fullExportText += exporter.exportMassFlows()
        fullExportText += exporter.exportDivSetting(simulationUnit - 10)

        self.logger.info("------------------------> END OF EXPORT <------------------------")

        if fullExportText[:1] == "\n":
            fullExportText = fullExportText[1:]
        controlFolder = os.path.split(hydCtrlPath)[0]
        if not (os.path.isdir(controlFolder)):
            os.makedirs(controlFolder)
        f = open(str(hydCtrlPath), "w")
        f.truncate(0)
        f.write(fullExportText)
        f.close()

        self.cleanUpExportedElements()

        return hydCtrlPath

    def cleanUpExportedElements(self):
        for t in self.trnsysObj:
            # if isinstance(t, BlockItem):
            #     t.exportConnsString = ""
            #     t.exportInputName = "0"
            #     t.exportInitialInput = -1
            #     t.exportEquations = []
            #     t.trnsysConn = []
            #
            # if type(t) is Connection:
            #     t.exportConnsString = ""
            #     t.exportInputName = "0"
            #     t.exportInitialInput = -1
            #     t.exportEquations = []
            #     t.trnsysConn = []
            t.cleanUpAfterTrnsysExport()

    def sortTrnsysObj(self):
        res = self.trnsysObj.sort(key=self.sortId)
        for s in self.trnsysObj:
            self.logger.debug("s has tr id " + str(s.trnsysId) + " has dname " + s.displayName)

    def sortId(self, l1):
        """
        Sort function returning a sortable key
        Parameters
        ----------
        l1 : Block/Connection

        Returns
        -------

        """
        return l1.trnsysId

    def setName(self, newName):
        self.diagramName = newName

    def delBlocks(self):
        """
        Deletes the whole diagram

        Returns
        -------

        """
        while len(self.trnsysObj) > 0:
            self.logger.info("In deleting...")
            self.trnsysObj[0].deleteBlock()

        while len(self.groupList) > 1:
            self.groupList[-1].deleteGroup()

        while len(self.graphicalObj) > 0:
            self.graphicalObj[0].deleteBlock()

        self.logger.debug("Groups are " + str(self.groupList))

    def newDiagram(self):
        self.centralWidget.delBlocks()

        # global id
        # global trnsysID
        # global globalConnID

        # self.id = 0
        # self.trnsysID = 0
        # self.globalConnID = 0

        self.idGen.reset()
        # newDiagramDlg(self)
        self.showNewDiagramDlg()

    # Encoding / decoding
    def encode(self, filename, encodeList):
        """
        Encoding function. Not used. encodeDiagram is used instead
        Parameters
        ----------
        filename : str
        encodeList : :obj:`list` of :obj:`BlockItem` and :obj:`Connection`

        Returns
        -------

        """
        with open(filename, "w") as jsonfile:
            json.dump(encodeList, jsonfile, indent=4, sort_keys=True, cls=Encoder)

    def encodeDiagram(self, filename):
        """
        Encodes the diagram to a json file.

        Parameters
        ----------
        filename : str

        Returns
        -------

        """
        self.logger.info("filename is at encoder " + str(filename))
        # if filename != "":
        with open(filename, "w") as jsonfile:
            json.dump(self, jsonfile, indent=4, sort_keys=True, cls=Encoder)

    def decodeDiagram(self, filename, loadValue="load"):
        """
        Decodes a diagram saved as a json-file. It also checks which folders exist in the ddck-directory of the pro-
        ject. It deletes all folders in the ddck-directory, which neither have a corresponding blockItem in the json-
        file nor are the generic, hydraulic, or a Tes-folder. Such folders are created when an item is dropped, but not
        saved in the diagram-json afterwards.

        Parameters
        ----------
        filename : str

        Returns
        -------

        """

        self.logger.info("Decoding " + filename)
        with open(filename, "r") as jsonfile:
            blocklist = json.load(jsonfile, cls=Decoder, editor=self)

        if len(self.groupList) == 0:
            self.logger.debug("self.group is empty, adding default group")
            self.defaultGroup = Group(0, 0, 100, 100, self.diagramScene)
            self.defaultGroup.setName("defaultGroup")

        blockFolderNames = []

        for j in blocklist["Blocks"]:
            # print("J is " + str(j))

            for k in j:
                if isinstance(k, BlockItem):
                    k.setParent(self.diagramView)
                    k.changeSize()
                    self.diagramScene.addItem(k)
                    blockFolderNames.append(k.displayName)
                    # blockFolderNames.append(k.name + '_' + k.displayName)
                    # k.setBlockToGroup("defaultGroup")

                if isinstance(k, StorageTank):
                    self.logger.debug("Loading a Storage")
                    k.setParent(self.diagramView)
                    k.updateImage()

                if isinstance(k, Connection):
                    if k.toPort == None or k.fromPort == None:
                        continue
                    # name = k.displayName
                    # testFrom = k.fromPort
                    # testTo = k.toPort
                    self.logger.debug("Almost done with loading a connection")
                    # print("Connection displ name " + str(k.displayName))
                    # print("Connection fromPort" + str(k.fromPort))
                    # print("Connection toPort" + str(k.toPort))
                    # print("Connection from " + k.fromPort.parent.displayName + " to " + k.toPort.parent.displayName)
                    k.initLoad()
                    a = 1
                    # k.setConnToGroup("defaultGroup")

                if isinstance(k, GraphicalItem):
                    k.setParent(self.diagramView)
                    self.diagramScene.addItem(k)
                    # k.resizer.setPos(k.w, k.h)
                    # k.resizer.itemChange(k.resizer.ItemPositionChange, k.resizer.pos())

                if isinstance(k, dict):
                    if "__idDct__" in k:
                        # here we don't set the ids because the copyGroup would need access to idGen
                        self.logger.debug("Found the id dict while loading, not setting the ids")
                        # global globalID
                        # global trnsysID
                        # global globalConnID

                        self.idGen.setID(k["GlobalId"])
                        self.idGen.setTrnsysID(k["trnsysID"])
                        self.idGen.setConnID(k["globalConnID"])
                        # self.idGen.setBlockID()

                    if "__nameDct__" in k:
                        self.logger.debug("Found the name dict while loading")
                        if loadValue == "load":
                            self.diagramName = k["DiagramName"]
                            # self.projectFolder = k["ProjectFolder"]

        blockFolderNames.append("generic")
        blockFolderNames.append("hydraulic")
        blockFolderNames.append("weather")
        blockFolderNames.append("control")

        ddckFolder = os.path.join(self.projectFolder, "ddck")
        ddckFolders = os.listdir(ddckFolder)
        additionalFolders = []

        for folder in ddckFolders:
            if folder not in blockFolderNames and "StorageTank" not in folder:
                additionalFolders.append(folder)

        if len(additionalFolders) > 0:
            warnBox = QMessageBox()
            warnBox.setWindowTitle("Additional ddck-folders")

            if len(additionalFolders) == 1:
                text = "The following ddck-folder does not have a corresponding component in the diagram:"
            else:
                text = "The following ddck-folders do not have a corresponding component in the diagram:"

            for folder in additionalFolders:
                text += "\n\t" + folder

            warnBox.setText(text)
            warnBox.setStandardButtons(QMessageBox.Ok)
            warnBox.setDefaultButton(QMessageBox.Ok)
            warnBox.exec()

        for t in self.trnsysObj:
            t.assignIDsToUninitializedValuesAfterJsonFormatMigration(self.idGen)

            self.logger.debug("Tr obj is" + str(t) + " " + str(t.trnsysId))
            if hasattr(t, "isTempering"):
                self.logger.debug("tv has " + str(t.isTempering))

    def exportSvg(self):
        """
        For exporting a svg file (text is still too large)
        Returns
        -------

        """
        generator = QSvgGenerator()
        generator.setResolution(300)
        generator.setSize(QSize(self.diagramScene.width(), self.diagramScene.height()))
        # generator.setViewBox(QRect(0, 0, 800, 800))
        generator.setViewBox(self.diagramScene.sceneRect())
        generator.setFileName("VectorGraphicsExport.svg")

        painter = QPainter()
        painter.begin(generator)
        painter.setRenderHint(QPainter.Antialiasing)
        self.diagramScene.render(painter)
        painter.end()

    def copyElements(self):
        """
        Copies elements
        Returns
        -------

        """
        clipboardGroup = copyGroup(self)
        self.logger.debug(self.diagramScene.elementsInRect())

        for t in self.diagramScene.elementsInRect():
            self.logger.debug("element in rect is" + str(t))
            clipboardGroup.trnsysObj.append(t)

        self.saveToClipBoard(clipboardGroup)

    def saveToClipBoard(self, copyList):
        filename = "clipboard.json"

        with open(filename, "w") as jsonfile:
            json.dump(copyList, jsonfile, indent=4, sort_keys=True, cls=Encoder)

        self.logger.debug("Copy complete!")

    def pasteFromClipBoard(self):
        filename = "clipboard.json"

        with open(filename, "r") as jsonfile:
            blocklist = json.load(jsonfile, cls=DecoderPaste, editor=self)

        for j in blocklist["Blocks"]:
            # print("J is " + str(j))

            for k in j:
                if isinstance(k, BlockItem):
                    # k.setParent(self.diagramView)
                    k.changeSize()
                    self.copyGroupList.addToGroup(k)

                    for inp in k.inputs:
                        inp.id = self.idGen.getID()
                    for out in k.outputs:
                        out.id = self.idGen.getID()

                if isinstance(k, StorageTank):
                    self.logger.debug("Loading a Storage")
                    k.updateImage()

                if isinstance(k, GraphicalItem):
                    k.setParent(self.diagramView)
                    self.diagramScene.addItem(k)
                    # k.resizer.setPos(k.w, k.h)
                    # k.resizer.itemChange(k.resizer.ItemPositionChange, k.resizer.pos())

                if isinstance(k, Connection):
                    self.logger.debug("Almost done with loading a connection")
                    k.initLoad()
                    for corners in k.getCorners():
                        # copyGroupList.trnsysObj.append(k)
                        self.copyGroupList.addToGroup(corners)

                if isinstance(k, dict):
                    pass

                    # print("Global id is " + str(globalID))
                    # print("trnsys id is " + str(trnsysID))

        # global copyMode
        # global selectionMode
        # global selectionMode
        # global pasting

        self.copyMode = False
        self.selectionMode = False

        self.diagramScene.addItem(self.copyGroupList)
        self.copyGroupList.setFlags(self.copyGroupList.ItemIsMovable)

        self.pasting = True

        # for t in self.trnsysObj:
        #     print("Tr obj is" + str(t) + " " + str(t.trnsysId))

    def clearCopyGroup(self):

        for it in self.copyGroupList.childItems():
            self.copyGroupList.removeFromGroup(it)

        self.pasting = False

    def createSelectionGroup(self, selectionList):
        for t in selectionList:
            if isinstance(t, BlockItem):
                self.selectionGroupList.addToGroup(t)
            if isinstance(t, GraphicalItem):
                self.selectionGroupList.addToGroup(t)

        self.multipleSelectedMode = False
        self.selectionMode = False

        self.diagramScene.addItem(self.selectionGroupList)
        self.selectionGroupList.setFlags(self.selectionGroupList.ItemIsMovable)

        self.itemsSelected = True

    def clearSelectionGroup(self):
        for it in self.selectionGroupList.childItems():
            self.selectionGroupList.removeFromGroup(it)

        self.itemsSelected = False

    # Saving related
    def save(self, showWarning=True):
        """
        If saveas has not been used, diagram will be saved in "/diagrams"
        If saveas has been used, diagram will be saved in self.saveAsPath
        Returns
        -------

        """
        self.diagramName = os.path.split(self.projectFolder)[-1] + ".json"
        diagramPath = os.path.join(self.projectFolder, self.diagramName)

        if os.path.isfile(diagramPath) and showWarning:
            qmb = QMessageBox(self)
            qmb.setText("Warning: " + "This diagram name exists already. Do you want to overwrite or cancel?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()

            if ret != QMessageBox.Save:
                self.logger.info("Canceling")
                return

            self.logger.info("Overwriting")
            self.encodeDiagram(diagramPath)

        self.encodeDiagram(diagramPath)
        msgb = QMessageBox(self)
        msgb.setText("Saved diagram at " + diagramPath)
        msgb.exec()

    def saveToProject(self):
        projectPath = self.projectPath

    def renameDiagram(self, newName):
        """

        Parameters
        ----------
        newName

        Returns
        -------

        """

        if self.saveAsPath.name != "":
            # print("Path name is " + self.saveAsPath.name)
            if newName + ".json" in self.saveAsPath.glob("*"):
                QMessageBox(
                    self, "Warning", "This diagram name exists already in the directory." " Please rename this diagram"
                )
            else:
                self.saveAsPath = _pl.Path(
                    self.saveAsPath.stem[0 : self.saveAsPath.name.index(self.diagramName)] + newName
                )

        self.diagramName = newName
        self.parent().currentFile = newName
        # fromPath = self.projectFolder
        # destPath = os.path.dirname(__file__)
        # destPath = os.path.join(destPath, 'default')
        # destPath = os.path.join(destPath, newName)
        # os.rename(fromPath, destPath)

        # print("Path is now: " + str(self.saveAsPath))
        # print("Diagram name is: " + self.diagramName)

    def saveAtClose(self):
        self.logger.info("saveaspath is " + str(self.saveAsPath))

        # closeDialog = closeDlg()
        # if closeDialog.closeBool:
        filepath = _pl.Path(_pl.Path(__file__).resolve().parent.joinpath("recent"))
        self.encodeDiagram(str(filepath.joinpath(self.diagramName + ".json")))

    # Mode related
    def setAlignMode(self, b):
        self.alignMode = True

    def setEditorMode(self, b):
        self.editorMode = b

    def setMoveDirectPorts(self, b):
        """
        Sets the bool moveDirectPorts. When mouse released in diagramScene, moveDirectPorts is set to False again
        Parameters
        ----------
        b : bool

        Returns
        -------

        """
        self.moveDirectPorts = b

    def setSnapGrid(self, b):
        self.snapGrid = b

    def setSnapSize(self, s):
        self.snapSize = s

    def setitemsSelected(self, b):
        self.itemsSelected = b

    # Misc
    def editGroups(self):
        self.showGroupsEditor()

    def setConnLabelVis(self, isVisible: bool) -> None:
        for c in self.trnsysObj:
            if isinstance(c, Connection):
                c.setLabelVisible(isVisible)
            if isinstance(c, BlockItem):
                c.label.setVisible(isVisible)
            if isinstance(c, TVentil):
                c.posLabel.setVisible(isVisible)

    def updateConnGrads(self):
        for t in self.trnsysObj:
            if isinstance(t, Connection):
                t.updateSegGrads()

    def findGroupByName(self, name):
        for g in self.groupList:
            if g.displayName == name:
                return g

        return None

    # Dialog calls
    def showBlockDlg(self, bl):
        c = BlockDlg(bl, self)

    def showPumpDlg(self, bl):
        c = PumpDlg(bl, self)

    def showDiagramDlg(self):
        c = diagramDlg(self)

    def showGenericPortPairDlg(self, bl):
        c = GenericPortPairDlg(bl, self)

    def showGroupChooserBlockDlg(self, bl):
        c = GroupChooserBlockDlg(bl, self)

    def showGroupChooserConnDlg(self, conn):
        c = GroupChooserConnDlg(conn, self)

    def showGroupDlg(self, group, itemList):
        c = groupDlg(group, self, itemList)

    def showHxDlg(self, hx):
        c = hxDlg(hx, self)

    def showNewDiagramDlg(self):
        c = newDiagramDlg(self)

    # Not used
    # def showNewPortDlg(self):
    #     c = newPortDlg

    def showSegmentDlg(self, seg):
        c = segmentDlg(seg, self)

    def showTVentilDlg(self, bl):
        c = TVentilDlg(bl, self)

    def showConfigStorageDlg(self, bl):
        c = ConfigureStorageDialog(bl, self)

    def showGroupsEditor(self):
        c = groupsEditor(self)

    def testFunctionInspection(self, *args):
        self.logger.debug("Ok, here is my log")
        self.logger.debug(int(args[0]) + 1)
        if len(self.connectionList) > 0:
            self.connectionList[0].highlightConn()

    def getConnection(self, n):
        return self.connectionList[int(n)]

    # Unused
    def create_icon(self, map_icon):
        map_icon.fill()
        painter = QPainter(map_icon)
        painter.fillRect(10, 10, 40, 40, QColor(88, 233, 252))
        # painter.setBrush(Qt.red)
        painter.setBrush(QColor(252, 136, 98))
        painter.drawEllipse(36, 2, 15, 15)
        painter.setBrush(Qt.yellow)
        painter.drawEllipse(20, 20, 20, 20)
        painter.end()

    def setTrnsysIdBack(self):
        self.idGen.trnsysID = max(t.trnsysId for t in self.trnsysObj)

    def findStorageCorrespPorts1(self, portList):
        """
        This function gets the ports on the other side of pipes connected to a port of the StorageTank. Unused

        Parameters
        ----------
        portList : :obj:`List` of :obj:`PortItems`

        Returns
        -------

        """

        res = []
        # print("Finding c ports")
        for p in portList:
            if len(p.connectionList) > 0:  # check if not >1 needed
                # connectionList[0] is the hidden connection created when the portPair is
                i = 0
                # while type(p.connectionList[i].fromPort.parent) is StorageTank and type(p.connectionList[i].toPort.parent) is StorageTank:
                while (p.connectionList[i].fromPort.parent) == (p.connectionList[i].toPort.parent):
                    i += 1
                if len(p.connectionList) >= i + 1:
                    if p.connectionList[i].fromPort is p:
                        res.append(p.connectionList[i].toPort)
                    elif p.connectionList[i].toPort is p:
                        res.append(p.connectionList[i].fromPort)
                    else:
                        self.logger.debug("Port is not fromPort nor toPort")

        # [print(p.parent.displayName) for p in res]
        return res

    def delGroup(self):
        """
        This is used for deleting the first connected componts group found by BFS, unused
        Returns
        -------

        """
        for bl in self.blockList:
            bl.deleteBlock()

    def testFunction(self):
        """
        This function tests whether the exporting function is working correctly by comparing
        an exported file to a reference file.
        Warning message will be shown if any difference is found between the files.
        -------
        Things to note : The fileDir must be changed to corresponding directories on the PC

        """

        i = 0
        self.tester = Test_Export()
        self.testPassed = True
        msg = QMessageBox(self)
        msg.setWindowTitle("Test Result")
        # fileDir = 'U:/Desktop/TrnsysGUI/trnsysGUI/'
        # examplesFilePath = fileDir + 'examplesNewEncoding/'
        # exportedFilePath = fileDir + 'export_test/'
        # originalFilePath = fileDir + 'Reference/'

        if getattr(sys, "frozen", False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)  # This is your Project Root
        examplesFilePath = os.path.join(ROOT_DIR, "examples")
        exportedFilePath = os.path.join(ROOT_DIR, "export_test")
        originalFilePath = os.path.join(ROOT_DIR, "Reference")

        exportedFileList = []
        originalFileList = []
        exampleFileList = []

        errorList1 = []
        errorLIst2 = []

        fileNoList = []

        msg.setText("Test in progress")
        msg.show()

        QCoreApplication.processEvents()

        # Clear the window
        # self.delBlocks()

        # open, decode and export every example file

        self.testEnabled = True
        for files in os.listdir(examplesFilePath):
            fileName = os.path.join(examplesFilePath, files)
            exampleFileList.append(fileName)
            self.decodeDiagram(fileName)
            # Export example files
            self.exportHydraulics()
            self.delBlocks()
        self.testEnabled = False

        # get all files from exportedFile folder and Original folder
        self.tester.retrieveFiles(exportedFilePath, originalFilePath, exportedFileList, originalFileList)

        # check if exported files exist inside reference folder
        j = 0
        while j < len(exportedFileList):
            if not self.tester.checkFileExists(exportedFileList[j], originalFileList):
                self.existReference = False
                testDlg = TestDlg(exportedFileList[j])
                if testDlg.exportBool:
                    self.delBlocks()
                    self.decodeDiagram(exampleFileList[j])
                    self.exportHydraulics()
                    self.delBlocks()
                self.existReference = True
            j += 1

        # Retrieve newly added files if any
        self.tester.retrieveFiles(exportedFilePath, originalFilePath, exportedFileList, originalFileList)

        # check if the files are identical
        fileNoList, self.testPassed = self.tester.checkFiles(exportedFileList, originalFileList)
        # i, self.testPassed = self.tester.checkFiles(exportedFileList, originalFileList)

        if self.testPassed:
            msg.setText("All files tested, no discrepancy found")
            msg.exec_()
        else:
            for fileNo in fileNoList:
                errorFile = originalFileList[fileNo]
                errorList1, errorList2 = self.tester.showDifference(exportedFileList[fileNo], originalFileList[fileNo])
                msg.setText("%d files tested, discrepancy found in %s" % ((fileNo + 1), errorFile))
                msg.exec_()
                DifferenceDlg(self, errorList1, errorList2, originalFileList[fileNo])
            # errorFile = originalFileList[i]
            # errorList1, errorList2 = self.tester.showDifference(exportedFileList[i], originalFileList[i])
            # msg.setText("%d files tested, discrepancy found in %s" % ((i + 1), errorFile))
            # msg.exec_()
            # DifferenceDlg(self, errorList1, errorList2)

        # Disable test and delete the exported files
        self.tester.deleteFiles(exportedFilePath)

    def printPDF(self):
        """
        ---------------------------------------------
        Export diagram as pdf onto specified folder
        fn = user input directory
        ---------------------------------------------
        """
        fn, _ = QFileDialog.getSaveFileName(self, "Export PDF", None, "PDF files (.pdf);;All Files()")
        if fn != "":
            if QFileInfo(fn).suffix() == "":
                fn += ".pdf"
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOrientation(QPrinter.Landscape)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(fn)
            painter = QPainter(printer)
            self.diagramScene.render(painter)
            painter.end()
            self.logger.info("File exported to %s" % fn)

    def setProjectPath(self):
        """
        This method is called when the 'Set Path' button for the file explorers is clicked.
        It sets the project path to the one defined by the user and updates the root path of every
        item inside the main window.
        If the path defined by the user doesn't exist. Creates that path.
        """
        self.projectPath = str(QFileDialog.getExistingDirectory(self, "Select Project Path"))
        if self.projectPath != "":
            self.PPL.setText(self.projectPath)
            # self.addButton.setEnabled(True)
            # self.delButton.setEnabled(True)

            loadPath = os.path.join(self.projectPath, "ddck")
            if not os.path.exists(loadPath):
                os.makedirs(loadPath)

            self.createConfigBrowser(self.projectPath)
            self.copyGenericFolder(self.projectPath)
            self.createHydraulicDir(self.projectPath)
            self.createWeatherAndControlDirs(self.projectPath)
            self.createDdckTree(loadPath)

            for o in self.trnsysObj:
                if hasattr(o, "updateTreePath"):
                    o.updateTreePath(self.projectPath)
                elif hasattr(o, "createControlDir"):
                    o.createControlDir()

    def openProject(self):
        self.projectPath = str(QFileDialog.getExistingDirectory(self, "Select Project Path"))
        if self.projectPath != "":
            test = self.parent()

            self.parent().newDia()
            self.PPL.setText(self.projectPath)
            loadPath = os.path.join(self.projectPath, "ddck")

            self.createConfigBrowser(self.projectPath)
            self.copyGenericFolder(self.projectPath)
            self.createHydraulicDir(self.projectPath)
            self.createWeatherAndControlDirs(self.projectPath)
            self.createDdckTree(loadPath)
            # todo : open diagram
            # todo : add files into list

    def createDdckTree(self, loadPath):
        treeToRemove = self.findChild(QTreeView, "ddck")
        try:
            # treeToRemove.hide()
            treeToRemove.deleteLater()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")
        if self.projectPath == "":
            loadPath = os.path.join(loadPath, "ddck")
        if not os.path.exists(loadPath):
            os.makedirs(loadPath)
        self.model = MyQFileSystemModel()
        self.model.setRootPath(loadPath)
        self.model.setName("ddck")
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(loadPath))
        self.tree.setObjectName("ddck")
        self.tree.setMinimumHeight(600)
        self.tree.setSortingEnabled(True)
        self.splitter.insertWidget(0, self.tree)

    def createConfigBrowser(self, loadPath):
        self.layoutToRemove = self.findChild(QHBoxLayout, "Config_Layout")
        try:
            # treeToRemove.hide()
            self.layoutToRemove.deleteLater()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")

        runConfigData = self._getPackageResourceData("templates/run.config")
        runConfigPath = _pl.Path(loadPath) / "run.config"
        runConfigPath.write_bytes(runConfigData)

        self.HBox = QHBoxLayout()
        self.refreshButton = QPushButton(self)
        self.refreshButton.setIcon(_img.ROTATE_TO_RIGHT_PNG.icon())
        self.refreshButton.clicked.connect(self.refreshConfig)
        self.model = MyQFileSystemModel()
        self.model.setRootPath(loadPath)
        self.model.setName("Config File")
        self.model.setFilter(QDir.Files)
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(loadPath))
        self.tree.setObjectName("config")
        self.tree.setFixedHeight(60)
        self.tree.setSortingEnabled(False)
        self.HBox.addWidget(self.refreshButton)
        self.HBox.addWidget(self.tree)
        self.HBox.setObjectName("Config_Layout")
        self.fileBrowserLayout.addLayout(self.HBox)

    def createProjectFolder(self):
        if not os.path.exists(self.projectFolder):
            os.makedirs(self.projectFolder)

    def refreshConfig(self):
        # configPath = os.path.dirname(__file__)
        # configPath = os.path.join(configPath, 'project')
        # configPath = os.path.join(configPath, self.date_time)
        # emptyConfig = os.path.join(configPath, 'run.config')
        if self.projectPath == "":
            localPath = self.projectFolder
        else:
            localPath = self.projectPath

        self.configToEdit = os.path.join(localPath, "run.config")
        os.remove(self.configToEdit)
        shutil.copy(self.emptyConfig, localPath)
        self.configToEdit = os.path.join(localPath, "run.config")

        localDdckPath = os.path.join(localPath, "ddck")
        with open(self.configToEdit, "r") as file:
            lines = file.readlines()
        localPathStr = "string LOCAL$ %s" % str(localDdckPath)
        # localPathStr.replace('/', '\\')
        lines[21] = localPathStr + "\n"

        with open(self.configToEdit, "w") as file:
            file.writelines(lines)

        # print(localPathStr)
        self.userInputList()

    def userInputList(self):
        self.logger.debug(self.fileList)
        dia = FileOrderingDialog(self.fileList, self)

    def copyGenericFolder(self, loadPath):
        genericFolderPath = _pl.Path(loadPath) / "ddck" / "generic"

        if not genericFolderPath.exists():
            self.logger.info("Creating %s", genericFolderPath)
            genericFolderPath.mkdir()

        headData = self._getPackageResourceData("templates/generic/head.ddck")
        self.logger.info("Copying head.ddck")
        (genericFolderPath / "head.ddck").write_bytes(headData)

        endData = self._getPackageResourceData("templates/generic/end.ddck")
        self.logger.info("Copying end.ddck")
        (genericFolderPath / "end.ddck").write_bytes(endData)

    @staticmethod
    def _getPackageResourceData(resourcePath):
        data = _pu.get_data(_tgui.__name__, resourcePath)
        assert data, f"{resourcePath} package resource not found"
        return data

    def createHydraulicDir(self, projectPath):

        self.hydraulicFolder = os.path.join(projectPath, "ddck")
        self.hydraulicFolder = os.path.join(self.hydraulicFolder, "hydraulic")

        if not os.path.exists(self.hydraulicFolder):
            self.logger.info("Creating " + self.hydraulicFolder)
            os.makedirs(self.hydraulicFolder)

    def createWeatherAndControlDirs(self, projectPath):

        ddckFolder = os.path.join(projectPath, "ddck")
        weatherFolder = os.path.join(ddckFolder, "weather")
        controlFolder = os.path.join(ddckFolder, "control")

        if not os.path.exists(weatherFolder):
            self.logger.info("Creating " + weatherFolder)
            os.makedirs(weatherFolder)

        if not os.path.exists(controlFolder):
            self.logger.info("Creating " + controlFolder)
            os.makedirs(controlFolder)

    # def addFile(self):
    #     fileName = QFileDialog.getOpenFileName(self, "Load file", filter="*.ddck")[0]
    #     simpFileName = fileName.split('/')[-1]
    #     loadPath = os.path.join(self.projectPath, 'ddck')
    #     loadPath = os.path.join(loadPath, simpFileName)
    #     if fileName != '':
    #         print("file loaded into %s" % loadPath)
    #         if Path(loadPath).exists():
    #             qmb = QMessageBox()
    #             qmb.setText("Warning: " +
    #                         "A file with the same name exists already. Do you want to overwrite or cancel?")
    #             qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
    #             qmb.setDefaultButton(QMessageBox.Cancel)
    #             ret = qmb.exec()
    #             if ret == QMessageBox.Save:
    #                 print("Overwriting")
    #                 # continue
    #             else:
    #                 print("Canceling")
    #                 return
    #         shutil.copy(fileName, loadPath)
    # def printEMF(self):
    #     """
    #                 ---------------------------------------------
    #                 Export diagram as EMF onto specified folder
    #                 fn = user input directory
    #                 ---------------------------------------------
    #             """
    #     fn, _ = QFileDialog.getSaveFileName(self, 'Export EMF', None, 'EMF files (.emf);;All Files()')
    #     if fn != '':
    #         if QFileInfo(fn).suffix() == "": fn += '.jpg'
    #         printer = QPrinter(QPrinter.HighResolution)
    #         printer.setOrientation(QPrinter.Landscape)
    #         printer.setOutputFormat(QPrinter.PdfFormat)
    #         printer.setOutputFileName(fn)
    #         painter = QPainter(printer)
    #         self.diagramScene.render(painter)
    #         painter.end()
    #         print("File exported to %s" % fn)
