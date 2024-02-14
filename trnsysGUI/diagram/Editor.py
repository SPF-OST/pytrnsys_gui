# pylint: skip-file
# type: ignore

import json
import math as _math
import os
import pathlib as _pl
import pkgutil as _pu
import shutil
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtPrintSupport as _qtp
import PyQt5.QtWidgets as _qtw

import pytrnsys.trnsys_util.deckUtils as _du
import pytrnsys.utils.result as _res
import trnsysGUI as _tgui
import trnsysGUI.names.manager as _nm
import trnsysGUI.connection.names as _cnames
import trnsysGUI.console as _con
import trnsysGUI.diagram.Encoder as _enc
import trnsysGUI.errors as _err
import trnsysGUI.errors as _errs
import trnsysGUI.hydraulicLoops.edit as _hledit
import trnsysGUI.hydraulicLoops.migration as _hlmig
import trnsysGUI.hydraulicLoops.model as _hlm
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.placeholders as _ph
from trnsysGUI.BlockDlg import BlockDlg
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Export import Export
from trnsysGUI.FileOrderingDialog import FileOrderingDialog
from trnsysGUI.GenericPortPairDlg import GenericPortPairDlg
from trnsysGUI.GraphicalItem import GraphicalItem
from trnsysGUI.LibraryModel import LibraryModel
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel  # type: ignore[attr-defined]
from trnsysGUI.MyQTreeView import MyQTreeView  # type: ignore[attr-defined]
from trnsysGUI.PortItemBase import PortItemBase
from trnsysGUI.TVentil import TVentil
from trnsysGUI.TVentilDlg import TVentilDlg
from trnsysGUI.connection.connectionBase import ConnectionBase
from trnsysGUI.connection.createDoublePipeConnectionCommand import CreateDoublePipeConnectionCommand
from trnsysGUI.connection.createSinglePipeConnectionCommand import CreateSinglePipeConnectionCommand
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection
from trnsysGUI.connection.singlePipeConnection import SinglePipeConnection
from trnsysGUI.diagram.Decoder import Decoder
from trnsysGUI.diagram.scene import Scene
from trnsysGUI.diagram.view import View
from trnsysGUI.diagramDlg import diagramDlg
from trnsysGUI.doublePipeBlockDlg import DoublePipeBlockDlg
from trnsysGUI.doublePipePortItem import DoublePipePortItem
from trnsysGUI.hxDlg import hxDlg
from trnsysGUI.idGenerator import IdGenerator
from trnsysGUI.segmentDialog import SegmentDialog
from trnsysGUI.singlePipePortItem import SinglePipePortItem
from trnsysGUI.storageTank.ConfigureStorageDialog import ConfigureStorageDialog
from trnsysGUI.storageTank.widget import StorageTank
from . import _sizes


class Editor(_qtw.QWidget):
    def __init__(self, parent, projectFolder, jsonPath, loadValue, logger):
        super().__init__(parent)

        self.logger = logger

        self.logger.info("Initializing the diagram editor")

        self.projectFolder = projectFolder

        self.diagramName = os.path.split(self.projectFolder)[-1] + ".json"
        self.saveAsPath = _pl.Path()
        self.idGen = IdGenerator()

        self.testEnabled = False
        self.existReference = True

        self.controlExists = 0
        self.controlDirectory = ""

        self.alignMode = False

        self.moveDirectPorts = False

        self.editorMode = 1

        # Related to the grid blocks can snap to
        self.snapGrid = False
        self.snapSize = 20

        self.trnsysPath = _pl.Path(r"C:\Trnsys18\Exe\TRNExe.exe")

        self.diagramScene = Scene(self)
        self.diagramView = View(self.diagramScene, self)

        # for file browser
        self.fileList = []

        if loadValue == "new" or loadValue == "json":
            self.createProjectFolder()

        self.fileBrowserLayout = _qtw.QVBoxLayout()
        self.pathLayout = _qtw.QHBoxLayout()
        self.projectPathLabel = _qtw.QLabel("Project Path:")
        self.PPL = _qtw.QLineEdit(self.projectFolder)
        self.PPL.setDisabled(True)

        self.pathLayout.addWidget(self.projectPathLabel)
        self.pathLayout.addWidget(self.PPL)
        self.scroll = _qtw.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.splitter = _qtw.QSplitter(
            _qtc.Qt.Vertical,
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

        self.loggingTextEdit = _qtw.QPlainTextEdit()
        self.loggingTextEdit.setReadOnly(True)

        self._setupWidgetHierarchy()

        self._currentlyDraggedConnectionFromPort = None
        self.connectionList = []
        self.trnsysObj = []

        ddckDirPath = _pl.Path(self.projectFolder) / "ddck"
        ddckDirFileOrDirNamesProvider = _nm.DdckDirFileOrDirNamesProvider(ddckDirPath)
        existingNames = []
        self.namesManager = _nm.NamesManager(existingNames, ddckDirFileOrDirNamesProvider)

        self.graphicalObj = []
        self.fluids = _hlm.Fluids.createDefault()
        self.hydraulicLoops = _hlm.HydraulicLoops([])

        self.copyGroupList = _qtw.QGraphicsItemGroup()
        self.selectionGroupList = _qtw.QGraphicsItemGroup()

        self.printerUnitnr = 0

        # Different colors for connLineColor
        colorsc = "red"
        linePx = 4
        if colorsc == "red":
            connLinecolor = _qtg.QColor(_qtc.Qt.red)
        elif colorsc == "blueish":
            connLinecolor = _qtg.QColor(3, 124, 193)  # Blue
        elif colorsc == "darkgray":
            connLinecolor = _qtg.QColor(140, 140, 140)  # Gray
        else:
            connLinecolor = _qtg.QColor(196, 196, 196)  # Gray

        # Only for displaying on-going creation of connection
        self.connLine = _qtc.QLineF()
        self.connLineItem = _qtw.QGraphicsLineItem(self.connLine)
        self.connLineItem.setPen(_qtg.QPen(connLinecolor, linePx))
        self.connLineItem.setVisible(False)
        self.diagramScene.addItem(self.connLineItem)

        # For line that shows quickly up when using the align mode
        self.alignYLine = _qtc.QLineF()
        self.alignYLineItem = _qtw.QGraphicsLineItem(self.alignYLine)
        self.alignYLineItem.setPen(_qtg.QPen(_qtg.QColor(196, 249, 252), 2))
        self.alignYLineItem.setVisible(False)
        self.diagramScene.addItem(self.alignYLineItem)

        # For line that shows quickly up when using align mode
        self.alignXLine = _qtc.QLineF()
        self.alignXLineItem = _qtw.QGraphicsLineItem(self.alignXLine)
        self.alignXLineItem.setPen(_qtg.QPen(_qtg.QColor(196, 249, 252), 2))
        self.alignXLineItem.setVisible(False)
        self.diagramScene.addItem(self.alignXLineItem)

        if loadValue == "load" or loadValue == "copy":
            self._decodeDiagram(os.path.join(self.projectFolder, self.diagramName), loadValue=loadValue)
        elif loadValue == "json":
            self._decodeDiagram(jsonPath, loadValue=loadValue)

    def _setupWidgetHierarchy(self):
        libraryBrowserView = self._createLibraryBrowserView()
        self.contextInfoList = _qtw.QListWidget()

        libraryBrowserAndContextInfoSplitter = _qtw.QSplitter(_qtc.Qt.Orientation.Vertical)
        libraryBrowserAndContextInfoSplitter.addWidget(libraryBrowserView)
        libraryBrowserAndContextInfoSplitter.addWidget(self.contextInfoList)
        _sizes.setRelativeSizes(
            libraryBrowserAndContextInfoSplitter, [libraryBrowserView, self.contextInfoList], [3, 1]
        )

        self._consoleWidget = _con.QtConsoleWidget()

        logAndConsoleTabs = _qtw.QTabWidget()
        logAndConsoleTabs.addTab(self.loggingTextEdit, "Logging")
        logAndConsoleTabs.addTab(self._consoleWidget, "IPython console")

        diagramAndTabsSplitter = _qtw.QSplitter(_qtc.Qt.Orientation.Vertical)
        diagramAndTabsSplitter.addWidget(self.diagramView)
        diagramAndTabsSplitter.addWidget(logAndConsoleTabs)
        _sizes.setRelativeSizes(diagramAndTabsSplitter, [self.diagramView, logAndConsoleTabs], [3, 1])

        fileBrowserWidget = _qtw.QWidget()
        fileBrowserWidget.setLayout(self.fileBrowserLayout)

        mainSplitter = _qtw.QSplitter(_qtc.Qt.Orientation.Horizontal)
        mainSplitter.addWidget(libraryBrowserAndContextInfoSplitter)
        mainSplitter.addWidget(diagramAndTabsSplitter)
        mainSplitter.addWidget(fileBrowserWidget)
        _sizes.setRelativeSizes(
            mainSplitter, [libraryBrowserAndContextInfoSplitter, diagramAndTabsSplitter, fileBrowserWidget], [1, 5, 1]
        )

        topLevelLayout = _qtw.QGridLayout(self)
        topLevelLayout.addWidget(mainSplitter)

    @staticmethod
    def _createLibraryBrowserView():

        componentNamesWithIcon = [
            ("Connector", _img.CONNECTOR_SVG.icon()),
            ("TeePiece", _img.TEE_PIECE_SVG.icon()),
            ("DPTee", _img.DP_TEE_PIECE_SVG.icon()),
            ("SPCnr", _img.SINGLE_DOUBLE_PIPE_CONNECTOR_SVG.icon()),
            ("DPCnr", _img.DOUBLE_DOUBLE_PIPE_CONNECTOR_SVG.icon()),
            ("TVentil", _img.T_VENTIL_SVG.icon()),
            ("WTap_main", _img.TAP_MAINS_SVG.icon()),
            ("WTap", _img.TAP_SVG.icon()),
            ("Pump", _img.PUMP_SVG.icon()),
            ("Collector", _img.COLLECTOR_SVG.icon()),
            ("GroundSourceHx", _img.GROUND_SOURCE_HX_SVG.icon()),
            ("PV", _img.PV_SVG.icon()),
            ("HP", _img.HP_SVG.icon()),
            ("HPTwoHx", _img.HP_TWO_HX_SVG.icon()),
            ("HPDoubleDual", _img.HP_DOUBLE_DUAL_SVG.icon()),
            ("HPDual", _img.HP_DUAL_SVG.icon()),
            ("AirSourceHP", _img.AIR_SOURCE_HP_SVG.icon()),
            ("StorageTank", _img.STORAGE_TANK_SVG.icon()),
            ("IceStorage", _img.ICE_STORAGE_SVG.icon()),
            ("PitStorage", _img.PIT_STORAGE_SVG.icon()),
            ("IceStorageTwoHx", _img.ICE_STORAGE_TWO_HX_SVG.icon()),
            ("ExternalHx", _img.EXTERNAL_HX_SVG.icon()),
            ("Radiator", _img.RADIATOR_SVG.icon()),
            ("Boiler", _img.BOILER_SVG.icon()),
            ("Sink", _img.SINK_SVG.icon()),
            ("Source", _img.SOURCE_SVG.icon()),
            ("SourceSink", _img.SOURCE_SINK_SVG.icon()),
            ("Geotherm", _img.GEOTHERM_SVG.icon()),
            ("Water", _img.WATER_SVG.icon()),
            ("Crystalizer", _img.CRYSTALIZER_SVG.icon()),
            ("CSP_CR", _img.CENTRAL_RECEVIER_SVG.icon()),
            ("CSP_PT", _img.PT_FIELD_SVG.icon()),
            ("powerBlock", _img.STEAM_POWER_BLOCK_SVG.icon()),
            ("coldSaltTank", _img.SALT_TANK_COLD_SVG.icon()),
            ("hotSaltTank", _img.SALT_TANK_HOT_SVG.icon()),
            ("GenericBlock", _img.GENERIC_BLOCK_PNG.icon()),
            ("GraphicalItem", _img.GENERIC_ITEM_PNG.icon()),
        ]

        libItems = [_qtg.QStandardItem(icon, name) for name, icon in componentNamesWithIcon]

        libraryModel = LibraryModel()
        libraryModel.setColumnCount(0)
        for i in libItems:
            libraryModel.appendRow(i)

        libraryBrowserView = _qtw.QListView()
        libraryBrowserView.setGridSize(_qtc.QSize(65, 65))
        libraryBrowserView.setResizeMode(_qtw.QListView.Adjust)
        libraryBrowserView.setModel(libraryModel)
        libraryBrowserView.setViewMode(libraryBrowserView.IconMode)
        libraryBrowserView.setDragDropMode(libraryBrowserView.DragOnly)
        return libraryBrowserView

    def isRunning(self):
        return self._consoleWidget.isRunning()

    def start(self) -> None:
        projectFolderPath = self.projectFolder
        self._consoleWidget.startInFolder(_pl.Path(projectFolderPath))

    def shutdown(self) -> None:
        self._consoleWidget.shutdown()

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
        self._currentlyDraggedConnectionFromPort = port

    def _createConnection(self, startPort, endPort) -> None:
        if startPort is not endPort:
            if (
                isinstance(startPort.parent, StorageTank)
                and isinstance(endPort.parent, StorageTank)
                and startPort.parent != endPort.parent
            ):
                msgSTank = _qtw.QMessageBox(self)
                msgSTank.setText("Storage Tank to Storage Tank connection is not working atm!")
                msgSTank.exec_()

            isValidSinglePipeConnection = isinstance(startPort, SinglePipePortItem) and isinstance(
                endPort, SinglePipePortItem
            )
            if isValidSinglePipeConnection:
                command = CreateSinglePipeConnectionCommand(startPort, endPort, self)
            elif isinstance(startPort, DoublePipePortItem) and isinstance(endPort, DoublePipePortItem):
                command = CreateDoublePipeConnectionCommand(startPort, endPort, self)
            else:
                raise AssertionError("Can only connect port items. Also, they have to be of the same type.")

            self.parent().undoStack.push(command)

    def sceneMouseMoveEvent(self, event):
        """
        This function is for dragging and connecting one port to another.
        When dragging, the fromPort will remain enlarged and black in color and when the toPort is hovered over, it will be
        enlarged and turn red.
        A port's details will also be displayed at the widget when they are hovered over.
        """
        fromPort = self._currentlyDraggedConnectionFromPort
        if not fromPort:
            return

        fromX = fromPort.scenePos().x()
        fromY = fromPort.scenePos().y()

        toX = event.scenePos().x()
        toY = event.scenePos().y()

        self.connLine.setLine(fromX, fromY, toX, toY)
        self.connLineItem.setLine(self.connLine)
        self.connLineItem.setVisible(True)

        hitPortItem = self._getToPortItemAtOrNone(fromPort, event)
        if not hitPortItem:
            return

        mousePosition = event.scenePos()

        portItemX = hitPortItem.scenePos().x()
        portItemY = hitPortItem.scenePos().y()

        distance = _math.sqrt((mousePosition.x() - portItemX) ** 2 + (mousePosition.y() - portItemY) ** 2)
        if distance <= 3.5:
            hitPortItem.enlargePortSize()
            hitPortItem.innerCircle.setBrush(hitPortItem.ashColorR)
            self.contextInfoList.clear()
            hitPortItem.debugprint()
        else:
            hitPortItem.resetPortSize()
            hitPortItem.innerCircle.setBrush(hitPortItem.visibleColor)
            self.contextInfoList.clear()
            fromPort.debugprint()

        fromPort.enlargePortSize()
        fromPort.innerCircle.setBrush(hitPortItem.visibleColor)

    def sceneMouseReleaseEvent(self, event):
        fromPort = self._currentlyDraggedConnectionFromPort

        self._currentlyDraggedConnectionFromPort = None
        self.connLineItem.setVisible(False)

        toPort = self._getToPortItemAtOrNone(fromPort, event)

        if not toPort:
            return

        if fromPort == toPort:
            return

        self._createConnection(fromPort, toPort)

    def _getToPortItemAtOrNone(
        self, fromPort: _tp.Optional[PortItemBase], event: _qtc.QEvent
    ) -> _tp.Optional[PortItemBase]:
        if not fromPort:
            return None

        mousePosition = event.scenePos()
        relevantPortItems = self._getRelevantHitPortItems(mousePosition, fromPort)
        if not relevantPortItems:
            return None

        numberOfHitPortsItems = len(relevantPortItems)
        if numberOfHitPortsItems > 1:
            self._showOverlappingPortItemsNotSupportedErrorMessage()
            return None

        hitPortItem = relevantPortItems[0]

        return hitPortItem

    @staticmethod
    def _showOverlappingPortItemsNotSupportedErrorMessage():
        errorMessage = (
            "Overlapping port items are not supported. Please move the containing components so that the "
            "port items don't overlap if you want to connect them."
        )
        _err.showErrorMessageBox(errorMessage, title="Not implemented")

    def _getRelevantHitPortItems(
        self, mousePosition: _qtc.QPointF, fromPort: PortItemBase
    ) -> _tp.Sequence[PortItemBase]:
        hitItems = self.diagramScene.items(mousePosition)
        relevantPortItems = [
            i for i in hitItems if isinstance(i, PortItemBase) and type(i) == type(fromPort) and not i.connectionList
        ]
        return relevantPortItems

    def cleanUpConnections(self):
        for c in self.connectionList:
            c.niceConn()

    def exportHydraulics(self, exportTo=_tp.Literal["ddck", "mfs"]):
        assert exportTo in ["ddck", "mfs"]

        if not self._isHydraulicConnected():
            messageBox = _qtw.QMessageBox()
            messageBox.setWindowTitle("Hydraulic not connected")
            messageBox.setText("You need to connect all port items before you can export the hydraulics.")
            messageBox.setStandardButtons(_qtw.QMessageBox.Ok)
            messageBox.exec()
            return

        self.logger.info("------------------------> START OF EXPORT <------------------------")

        self.sortTrnsysObj()

        fullExportText = ""

        ddckFolder = os.path.join(self.projectFolder, "ddck")

        if exportTo == "mfs":
            mfsFileName = self.diagramName.rsplit(".", 1)[0] + "_mfs.dck"
            exportPath = os.path.join(self.projectFolder, mfsFileName)
        elif exportTo == "ddck":
            exportPath = os.path.join(ddckFolder, "hydraulic", "hydraulic.ddck")

        if self._doesFileExistAndDontOverwrite(exportPath):
            return None

        self.logger.info("Printing the TRNSYS file...")

        if exportTo == "mfs":
            header = open(os.path.join(ddckFolder, "generic", "head.ddck"), "r", encoding="windows-1252")
            headerLines = header.readlines()
            for line in headerLines:
                if line[:4] == "STOP":
                    fullExportText += "STOP = 1 \n"
                else:
                    fullExportText += line
            header.close()
        elif exportTo == "ddck":
            SinglePipeTotals = _cnames.EnergyBalanceTotals.SinglePipe
            DoublePipeTotals = _cnames.EnergyBalanceTotals.DoublePipe

            simulatedSinglePipes = [
                o for o in self.trnsysObj if isinstance(o, SinglePipeConnection) and o.shallBeSimulated
            ]
            singlePipeEnergyBalanceEquations = ""
            if simulatedSinglePipes:
                singlePipeEnergyBalanceEquations = f"""\
EQUATIONS 2
*** single pipes
qSysOut_PipeLoss = {SinglePipeTotals.DISSIPATED}
qSysOut_{SinglePipeTotals.PIPE_INTERNAL_CHANGE} = {SinglePipeTotals.PIPE_INTERNAL_CHANGE}

"""
            simulatedDoublePipes = [
                o for o in self.trnsysObj if isinstance(o, DoublePipeConnection) and o.shallBeSimulated
            ]
            doublePipesEnergyBalanceEquations = ""
            if simulatedDoublePipes:
                doublePipesEnergyBalanceEquations = f"""\
EQUATIONS 3
*** double pipes
qSysOut_{DoublePipeTotals.DISSIPATION_TO_FAR_FIELD} = {DoublePipeTotals.DISSIPATION_TO_FAR_FIELD}
qSysOut_{DoublePipeTotals.PIPE_INTERNAL_CHANGE} = {DoublePipeTotals.PIPE_INTERNAL_CHANGE}
qSysOut_{DoublePipeTotals.SOIL_INTERNAL_CHANGE} = {DoublePipeTotals.SOIL_INTERNAL_CHANGE}
"""
            energyBalanceEquations = f"""\
*************************************
** BEGIN hydraulic.ddck
*************************************

*************************************
** Outputs to energy balance in kWh

** Following this naming standard : qSysIn_name, qSysOut_name, elSysIn_name, elSysOut_name

*************************************
{singlePipeEnergyBalanceEquations}
{doublePipesEnergyBalanceEquations}

"""

            fullExportText += energyBalanceEquations

        simulationUnit = 450
        simulationType = 9352
        descConnLength = 15

        exporter = self._createExporter()

        blackBoxProblem, blackBoxText = exporter.exportBlackBox(exportTo=exportTo)
        if blackBoxProblem:
            return None

        fullExportText += blackBoxText
        if exportTo == "mfs":
            fullExportText += exporter.exportMassFlows()
            fullExportText += exporter.exportPumpOutlets()
            fullExportText += exporter.exportDivSetting(simulationUnit - 10)

        fullExportText += exporter.exportSinglePipeParameters()
        fullExportText += exporter.exportDoublePipeParameters(exportTo=exportTo)

        fullExportText += exporter.exportParametersFlowSolver(simulationUnit, simulationType, descConnLength)

        fullExportText += exporter.exportInputsFlowSolver()
        fullExportText += exporter.exportOutputsFlowSolver(simulationUnit)
        fullExportText += exporter.exportFluids() + "\n"
        fullExportText += exporter.exportHydraulicLoops() + "\n"
        fullExportText += exporter.exportPipeAndTeeTypesForTemp(simulationUnit + 1)  # DC-ERROR
        fullExportText += exporter.exportSinglePipeEnergyBalanceVariables()
        fullExportText += exporter.exportDoublePipeEnergyBalanceVariables()

        fullExportText += exporter.exportMassFlowPrinter(self.printerUnitnr, 15)
        fullExportText += exporter.exportTempPrinter(self.printerUnitnr + 1, 15)

        if exportTo == "mfs":
            fullExportText += "CONSTANTS 1\nTRoomStore=1\n"
            fullExportText += "ENDS"

        self.logger.info("------------------------> END OF EXPORT <------------------------")

        if exportTo == "mfs":
            f = open(exportPath, "w")
            f.truncate(0)
            f.write(fullExportText)
            f.close()
        elif exportTo == "ddck":
            if fullExportText[:1] == "\n":
                fullExportText = fullExportText[1:]
            hydraulicFolder = os.path.split(exportPath)[0]
            if not (os.path.isdir(hydraulicFolder)):
                os.makedirs(hydraulicFolder)
            f = open(exportPath, "w")
            f.truncate(0)
            f.write(fullExportText)
            f.close()

        try:
            lines = _du.loadDeck(exportPath, eraseBeginComment=True, eliminateComments=True)
            _du.checkEquationsAndConstants(lines, exportPath)
        except Exception as error:
            errorMessage = f"An error occurred while exporting the system hydraulics: {error}"
            _errs.showErrorMessageBox(errorMessage)
            return None

        return exportPath

    def _createExporter(self) -> Export:
        massFlowContributors = self._getMassFlowContributors()
        exporter = Export(
            self.diagramName,
            massFlowContributors,
            self.hydraulicLoops.hydraulicLoops,
            self.fluids.fluids,
            self.logger,
            self,
        )
        return exporter

    def _getMassFlowContributors(self) -> _tp.Sequence[_ip.HasInternalPiping]:
        massFlowContributors = [o for o in self.trnsysObj if isinstance(o, _ip.HasInternalPiping)]
        return massFlowContributors

    def _isHydraulicConnected(self) -> bool:
        for obj in self.trnsysObj:
            if not isinstance(obj, _ip.HasInternalPiping):
                continue

            internalPiping = obj.getInternalPiping()

            for portItem in internalPiping.modelPortItemsToGraphicalPortItem.values():
                if not portItem.connectionList:
                    return False

        return True

    def _doesFileExistAndDontOverwrite(self, folderPath):
        if not _pl.Path(folderPath).exists():
            return False

        qmb = _qtw.QMessageBox(self)
        qmb.setText(f"Warning: {folderPath} already exists. Do you want to overwrite it or cancel?")
        qmb.setStandardButtons(_qtw.QMessageBox.Save | _qtw.QMessageBox.Cancel)
        qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
        ret = qmb.exec()

        if ret == _qtw.QMessageBox.Cancel:
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

        hydCtrlPath = os.path.join(ddckFolder, "control", "hydraulic_control.ddck")
        if _pl.Path(hydCtrlPath).exists():
            qmb = _qtw.QMessageBox(self)
            qmb.setText(
                "Warning: "
                + "The file hydraulic_control.ddck already exists in the control folder. Do you want to overwrite it or cancel?"
            )
            qmb.setStandardButtons(_qtw.QMessageBox.Save | _qtw.QMessageBox.Cancel)
            qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == _qtw.QMessageBox.Save:
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

        exporter = self._createExporter()

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

        return hydCtrlPath

    def sortTrnsysObj(self):
        self.trnsysObj.sort(key=self.sortId)
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
        self.hydraulicLoops.clear()

        while self.trnsysObj:
            trnsysObject = self.trnsysObj[0]
            if isinstance(trnsysObject, BlockItem):
                trnsysObject.deleteBlock()
            elif isinstance(trnsysObject, ConnectionBase):
                trnsysObject.deleteConn()
            else:
                raise AssertionError(f"Don't know how to delete {trnsysObject}.")

        while self.graphicalObj:
            self.graphicalObj[0].deleteBlock()

    # Encoding / decoding
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

        with open(filename, "w") as jsonfile:
            json.dump(self, jsonfile, indent=4, sort_keys=True, cls=_enc.Encoder)

    def _decodeDiagram(self, filename, loadValue="load"):
        self.logger.info("Decoding " + filename)
        with open(filename, "r") as jsonfile:
            blocklist = json.load(jsonfile, cls=Decoder, editor=self)

        blockFolderNames = []

        for j in blocklist["Blocks"]:
            for k in j:
                if isinstance(k, BlockItem):
                    k.setParent(self)
                    k.changeSize()
                    self.diagramScene.addItem(k)
                    blockFolderNames.append(k.displayName)

                if isinstance(k, StorageTank):
                    k.updateImage()

                if isinstance(k, GraphicalItem):
                    k.setParent(self.diagramView)
                    self.diagramScene.addItem(k)

                if isinstance(k, dict):
                    if "__idDct__" in k:
                        # here we don't set the ids because the copyGroup would need access to idGen
                        self.logger.debug("Found the id dict while loading, not setting the ids")

                        self.idGen.setID(k["GlobalId"])
                        self.idGen.setTrnsysID(k["trnsysID"])
                        self.idGen.setConnID(k["globalConnID"])

                    if "__nameDct__" in k:
                        self.logger.debug("Found the name dict while loading")
                        if loadValue == "load":
                            self.diagramName = k["DiagramName"]

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
            warnBox = _qtw.QMessageBox()
            warnBox.setWindowTitle("Additional ddck-folders")

            if len(additionalFolders) == 1:
                text = "The following ddck-folder does not have a corresponding component in the diagram:"
            else:
                text = "The following ddck-folders do not have a corresponding component in the diagram:"

            for folder in additionalFolders:
                text += "\n\t" + folder

            warnBox.setText(text)
            warnBox.setStandardButtons(_qtw.QMessageBox.Ok)
            warnBox.setDefaultButton(_qtw.QMessageBox.Ok)
            warnBox.exec()

        for t in self.trnsysObj:
            t.assignIDsToUninitializedValuesAfterJsonFormatMigration(self.idGen)

            if hasattr(t, "isTempering"):
                self.logger.debug("tv has " + str(t.isTempering))

        self._decodeHydraulicLoops(blocklist)

        self._setHydraulicLoopsOnStorageTanks()

        self._addNamesToNameValidator()

    def _decodeHydraulicLoops(self, blocklist) -> None:
        singlePipeConnections = [c for c in self.connectionList if isinstance(c, SinglePipeConnection)]
        if "hydraulicLoops" not in blocklist:
            hydraulicLoops = _hlmig.createLoops(singlePipeConnections, self.fluids.WATER)
        else:
            serializedHydraulicLoops = blocklist["hydraulicLoops"]
            hydraulicLoops = _hlm.HydraulicLoops.createFromJson(
                serializedHydraulicLoops, singlePipeConnections, self.fluids
            )

        self.hydraulicLoops = hydraulicLoops

    def _setHydraulicLoopsOnStorageTanks(self) -> None:
        for trnsysObject in self.trnsysObj:
            if not isinstance(trnsysObject, StorageTank):
                continue

            storageTank = trnsysObject

            storageTank.setHydraulicLoops(self.hydraulicLoops)

    def _addNamesToNameValidator(self) -> None:
        for trnsysObject in self.trnsysObj:
            self.namesManager.addName(trnsysObject.displayName)

    def exportDdckPlaceHolderValuesJsonFile(self) -> _res.Result[None]:
        if not self._isHydraulicConnected():
            return _res.Error("You need to connect all port items before you can export the hydraulics.")

        jsonFilePath = _pl.Path(self.projectFolder) / "DdckPlaceHolderValues.json"

        if jsonFilePath.is_dir():
            _qtw.QMessageBox.information(
                self,
                "Folder already exists",
                f"A folder already exits at f{jsonFilePath}. Chose a different location or delete the folder first.",
            )
            return None

        if jsonFilePath.is_file():
            pressedButton = _qtw.QMessageBox.question(
                self,
                "Overwrite file?",
                f"The file {jsonFilePath} already exists. Do you want to overwrite it or cancel?",
                buttons=(_qtw.QMessageBox.Save | _qtw.QMessageBox.Cancel),
                defaultButton=_qtw.QMessageBox.Cancel,
            )

            if pressedButton != _qtw.QMessageBox.Save:
                return None

        result = self.encodeDdckPlaceHolderValuesToJson(jsonFilePath)
        if _res.isError(result):
            return _res.error(result)

        _qtw.QMessageBox.information(
            self,
            "Saved successfully",
            f"Saved place holder values JSON file at {jsonFilePath}.",
            buttons=_qtw.QMessageBox.Ok,
        )

        return None

    def encodeDdckPlaceHolderValuesToJson(self, filePath: _pl.Path) -> _res.Result[None]:
        ddckDirNames = self._getDdckDirNames()

        result = _ph.getPlaceholderValues(ddckDirNames, self.trnsysObj, self.hydraulicLoops)
        if _res.isError(result):
            return _res.error(result)

        ddckPlaceHolderValuesDictionary = _res.value(result)

        jsonContent = json.dumps(ddckPlaceHolderValuesDictionary, indent=4, sort_keys=True)
        filePath.write_text(jsonContent)

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
            qmb = _qtw.QMessageBox(self)
            qmb.setText("Warning: " + "This diagram name exists already. Do you want to overwrite or cancel?")
            qmb.setStandardButtons(_qtw.QMessageBox.Save | _qtw.QMessageBox.Cancel)
            qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
            ret = qmb.exec()

            if ret != _qtw.QMessageBox.Save:
                self.logger.info("Canceling")
                return

            self.logger.info("Overwriting")
            self.encodeDiagram(diagramPath)

        self.encodeDiagram(diagramPath)
        if showWarning:
            msgb = _qtw.QMessageBox()
            msgb.setWindowTitle("Saved successfully")
            msgb.setText("Saved diagram at " + diagramPath)
            msgb.setStandardButtons(_qtw.QMessageBox.Ok)
            msgb.setDefaultButton(_qtw.QMessageBox.Ok)
            msgb.exec()

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
                _qtw.QMessageBox(
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

    def setConnLabelVis(self, isVisible: bool) -> None:
        for c in self.trnsysObj:
            if isinstance(c, ConnectionBase):
                c.setLabelVisible(isVisible)
            if isinstance(c, BlockItem):
                c.label.setVisible(isVisible)
            if isinstance(c, TVentil):
                c.posLabel.setVisible(isVisible)

    def updateConnGrads(self):
        for t in self.trnsysObj:
            if isinstance(t, ConnectionBase):
                t.updateSegGrads()

    # Dialog calls
    def showBlockDlg(self, bl):
        c = BlockDlg(bl, self)

    def showDoublePipeBlockDlg(self, bl):
        c = DoublePipeBlockDlg(bl, self)

    def showDiagramDlg(self):
        c = diagramDlg(self)

    def showGenericPortPairDlg(self, bl):
        c = GenericPortPairDlg(bl, self)

    def showHxDlg(self, hx):
        c = hxDlg(hx, self)

    def showSegmentDlg(self, seg):
        segmentDialog = SegmentDialog(seg.connection, self.namesManager)
        segmentDialog.exec()

    def showTVentilDlg(self, bl):
        c = TVentilDlg(bl, self)

    def showConfigStorageDlg(self, bl):
        c = ConfigureStorageDialog(bl, self)

    def getConnection(self, n):
        return self.connectionList[int(n)]

    # Unused
    def create_icon(self, map_icon):
        map_icon.fill()
        painter = _qtg.QPainter(map_icon)
        painter.fillRect(10, 10, 40, 40, _qtg.QColor(88, 233, 252))
        # painter.setBrush(Qt.red)
        painter.setBrush(_qtg.QColor(252, 136, 98))
        painter.drawEllipse(36, 2, 15, 15)
        painter.setBrush(_qtc.Qt.yellow)
        painter.drawEllipse(20, 20, 20, 20)
        painter.end()

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

        # [print(p.parent.newDisplayName) for p in res]
        return res

    def printPDF(self):
        """
        ---------------------------------------------
        Export diagram as pdf onto specified folder
        fn = user input directory
        ---------------------------------------------
        """
        fn, _ = _qtw.QFileDialog.getSaveFileName(self, "Export PDF", None, "PDF files (.pdf);;All Files()")
        if fn != "":
            if _qtc.QFileInfo(fn).suffix() == "":
                fn += ".pdf"
            printer = _qtp.QPrinter(_qtp.QPrinter.HighResolution)
            printer.setOrientation(_qtp.QPrinter.Landscape)
            printer.setOutputFormat(_qtp.QPrinter.PdfFormat)
            printer.setOutputFileName(fn)
            painter = _qtg.QPainter(printer)
            self.diagramScene.render(painter)
            painter.end()
            self.logger.info("File exported to %s" % fn)

    def createDdckTree(self, loadPath):
        treeToRemove = self.findChild(_qtw.QTreeView, "ddck")
        try:
            treeToRemove.deleteLater()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")
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
        self.layoutToRemove = self.findChild(_qtw.QHBoxLayout, "Config_Layout")
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

        self.HBox = _qtw.QHBoxLayout()
        self.refreshButton = _qtw.QPushButton(self)
        self.refreshButton.setIcon(_img.ROTATE_TO_RIGHT_PNG.icon())
        self.refreshButton.clicked.connect(self.refreshConfig)
        self.model = MyQFileSystemModel()
        self.model.setRootPath(loadPath)
        self.model.setName("Config File")
        self.model.setFilter(_qtc.QDir.Files)
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
        localPath = self.projectFolder

        self.configToEdit = os.path.join(localPath, "run.config")
        os.remove(self.configToEdit)
        shutil.copy(self.emptyConfig, localPath)
        self.configToEdit = os.path.join(localPath, "run.config")

        localDdckPath = os.path.join(localPath, "ddck")
        with open(self.configToEdit, "r") as file:
            lines = file.readlines()
        localPathStr = "string LOCAL$ %s" % str(localDdckPath)
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

    def createHydraulicDir(self, projectFolder):

        self.hydraulicFolder = os.path.join(projectFolder, "ddck")
        self.hydraulicFolder = os.path.join(self.hydraulicFolder, "hydraulic")

        if not os.path.exists(self.hydraulicFolder):
            self.logger.info("Creating " + self.hydraulicFolder)
            os.makedirs(self.hydraulicFolder)

    def createWeatherAndControlDirs(self, projectFolder):

        ddckFolder = os.path.join(projectFolder, "ddck")
        weatherFolder = os.path.join(ddckFolder, "weather")
        controlFolder = os.path.join(ddckFolder, "control")

        if not os.path.exists(weatherFolder):
            self.logger.info("Creating " + weatherFolder)
            os.makedirs(weatherFolder)

        if not os.path.exists(controlFolder):
            self.logger.info("Creating " + controlFolder)
            os.makedirs(controlFolder)

    def editHydraulicLoop(self, singlePipeConnection: SinglePipeConnection):
        assert isinstance(singlePipeConnection.fromPort, SinglePipePortItem)

        hydraulicLoop = self.hydraulicLoops.getLoopForExistingConnection(singlePipeConnection)
        _hledit.edit(hydraulicLoop, self.hydraulicLoops, self.fluids)

        self._updateGradients(hydraulicLoop)

    @staticmethod
    def _updateGradients(hydraulicLoop: _hlm.HydraulicLoop) -> None:
        for connection in hydraulicLoop.connections:
            connection.updateSegGrads()

    def _getDdckDirNames(self) -> _tp.Sequence[str]:
        ddckDirPath = _pl.Path(self.projectFolder) / "ddck"

        componentDdckDirPaths = list(ddckDirPath.iterdir())

        ddckDirNames = []
        for componentDirPath in componentDdckDirPaths:
            ddckDirNames.append(componentDirPath.name)

        return ddckDirNames

    def nameExists(self, name):
        for item in self.trnsysObj:
            if str(item.displayName).lower() == name.lower():
                return True
        return False

    def nameExistsInDdckFolder(self, name):
        projectFolderDdckPath = _pl.Path(self.projectFolder) / "ddck"
        projectDdckFiles = projectFolderDdckPath.iterdir()
        for file in projectDdckFiles:
            if file.name.lower() == name.lower():
                return True
        return False
