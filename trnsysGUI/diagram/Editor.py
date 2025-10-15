# pylint: skip-file
# type: ignore

import collections.abc as _cabc
import json
import math as _math
import os
import pathlib as _pl
import pkgutil as _pu
import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw
import pytrnsys.trnsys_util.deckUtils as _du

import trnsysGUI as _tgui
import trnsysGUI.components.factory as _cfactory
import trnsysGUI.connection.connectors.doublePipeConnectorBase as _dctor
import trnsysGUI.connection.names as _cnames
import trnsysGUI.console as _con
import trnsysGUI.diagram.Encoder as _enc
import trnsysGUI.hydraulicLoops.edit as _hledit
import trnsysGUI.hydraulicLoops.migration as _hlmig
import trnsysGUI.hydraulicLoops.model as _hlm
import trnsysGUI.internalPiping as _ip
import trnsysGUI.names.create as _nc
import trnsysGUI.names.manager as _nm
import trnsysGUI.names.rename as _rename
import trnsysGUI.names.undo as _nu
import trnsysGUI.segments.segmentItemBase as _sib
import trnsysGUI.storageTank.widget as _stwidget
import trnsysGUI.warningsAndErrors as _werrs
from trnsysGUI.BlockDlg import BlockDlg
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Export import Export
from trnsysGUI.GenericPortPairDlg import GenericPortPairDlg
from trnsysGUI.GraphicalItem import GraphicalItem
from trnsysGUI.LibraryModel import LibraryModel
from trnsysGUI.PortItemBase import PortItemBase
from trnsysGUI.TVentil import TVentil
from trnsysGUI.TVentilDlg import TVentilDlg
from trnsysGUI.connection.addDoublePipeConnectionCommand import (
    AddDoublePipeConnectionCommand,
)
from trnsysGUI.connection.addSinglePipeConnectionCommand import (
    AddSinglePipeConnectionCommand,
)
from trnsysGUI.connection.connectionBase import ConnectionBase
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
from . import fileSystemTreeView as _fst
from ..recentProjectsHandler import RecentProjectsHandler


class Editor(_qtw.QWidget, _ip.HasInternalPipingsProvider):
    def __init__(self, parent, projectFolder, jsonPath, loadValue, logger):
        super().__init__(parent)

        self.forceOverwrite = False
        self.logger = logger

        self.logger.info("Initializing the diagram editor")

        self.projectFolder = projectFolder

        self.diagramName = os.path.split(self.projectFolder)[-1] + ".json"
        self.saveAsPath = _pl.Path()
        self.idGen = IdGenerator()

        self.alignMode = False

        self.moveDirectPorts = False

        # Related to the grid blocks can snap to
        self.snapGrid = False
        self.snapSize = 20

        self.trnsysPath = _pl.Path(r"C:\Trnsys18\Exe\TRNExe.exe")

        self.diagramScene = Scene(self)
        self.diagramView = View(self.diagramScene, self)

        if loadValue == "new" or loadValue == "json":
            self.createProjectFolder()

        self.fileBrowserLayout = _qtw.QVBoxLayout()
        self.pathLayout = _qtw.QHBoxLayout()
        self.projectPathLabel = _qtw.QLabel("Project Path:")
        self.PPL = _qtw.QLineEdit(self.projectFolder)
        self.PPL.setDisabled(True)

        self.pathLayout.addWidget(self.projectPathLabel)
        self.pathLayout.addWidget(self.PPL)

        treeView = _fst.FileSystemTreeView(_pl.Path(self.projectFolder), self)

        self.fileBrowserLayout.addLayout(self.pathLayout)
        self.fileBrowserLayout.addWidget(treeView)

        if loadValue == "new" or loadValue == "json":
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
        ddckDirFileOrDirNamesProvider = _nm.DdckDirFileOrDirNamesProvider(
            ddckDirPath
        )
        existingNames = []
        self.namesManager = _nm.NamesManager(
            existingNames, ddckDirFileOrDirNamesProvider
        )

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
            self._decodeDiagram(
                os.path.join(self.projectFolder, self.diagramName),
                loadValue=loadValue,
            )
        elif loadValue == "json":
            self._decodeDiagram(jsonPath, loadValue=loadValue)

    def _setupWidgetHierarchy(self):
        libraryBrowserView = self._createLibraryBrowserView()
        self.contextInfoList = _qtw.QListWidget()

        libraryBrowserAndContextInfoSplitter = _qtw.QSplitter(
            _qtc.Qt.Orientation.Vertical
        )
        libraryBrowserAndContextInfoSplitter.addWidget(libraryBrowserView)
        libraryBrowserAndContextInfoSplitter.addWidget(self.contextInfoList)
        _sizes.setRelativeSizes(
            libraryBrowserAndContextInfoSplitter,
            [libraryBrowserView, self.contextInfoList],
            [3, 1],
        )

        self._consoleWidget = _con.QtConsoleWidget()

        logAndConsoleTabs = _qtw.QTabWidget()
        logAndConsoleTabs.addTab(self.loggingTextEdit, "Logging")
        logAndConsoleTabs.addTab(self._consoleWidget, "IPython console")

        diagramAndTabsSplitter = _qtw.QSplitter(_qtc.Qt.Orientation.Vertical)
        diagramAndTabsSplitter.addWidget(self.diagramView)
        diagramAndTabsSplitter.addWidget(logAndConsoleTabs)
        _sizes.setRelativeSizes(
            diagramAndTabsSplitter,
            [self.diagramView, logAndConsoleTabs],
            [3, 1],
        )

        fileBrowserWidget = _qtw.QWidget()
        fileBrowserWidget.setLayout(self.fileBrowserLayout)

        mainSplitter = _qtw.QSplitter(_qtc.Qt.Orientation.Horizontal)
        mainSplitter.addWidget(libraryBrowserAndContextInfoSplitter)
        mainSplitter.addWidget(diagramAndTabsSplitter)
        mainSplitter.addWidget(fileBrowserWidget)
        _sizes.setRelativeSizes(
            mainSplitter,
            [
                libraryBrowserAndContextInfoSplitter,
                diagramAndTabsSplitter,
                fileBrowserWidget,
            ],
            [1, 5, 1],
        )

        topLevelLayout = _qtw.QGridLayout(self)
        topLevelLayout.addWidget(mainSplitter)

    @staticmethod
    def _createLibraryBrowserView():
        libraryModel = LibraryModel()
        libraryModel.setColumnCount(0)

        componentsWithWarnings = _cfactory.getComponents()
        if componentsWithWarnings.hasWarnings():
            warningMessage = componentsWithWarnings.toWarningMessage()
            _werrs.showMessageBox(warningMessage, _werrs.Title.WARNING)
        components = componentsWithWarnings.value

        for component in components:
            item = _qtg.QStandardItem(component.icon, component.name)
            item.setEditable(False)
            libraryModel.appendRow(item)

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
                msgSTank.setText(
                    "Storage Tank to Storage Tank connection is not working atm!"
                )
                msgSTank.exec_()

            isValidSinglePipeConnection = isinstance(
                startPort, SinglePipePortItem
            ) and isinstance(endPort, SinglePipePortItem)
            isValidDoublePipeConnection = isinstance(
                startPort, DoublePipePortItem
            ) and isinstance(endPort, DoublePipePortItem)

            if isValidSinglePipeConnection:
                command = self._createCreateSinglePipeConnectionCommand(
                    startPort, endPort
                )
            elif isValidDoublePipeConnection:
                command = self._createCreateDoublePipeConnectionCommand(
                    startPort, endPort
                )
            else:
                raise AssertionError(
                    "Can only connect port items. Also, they have to be of the same type."
                )

            self.parent().undoStack.push(command)

    def _createCreateSinglePipeConnectionCommand(
        self, startPort: SinglePipePortItem, endPort: SinglePipePortItem
    ) -> AddSinglePipeConnectionCommand:
        displayName, undoNamingHelper = self._createDisplayAndUndoNamingHelper(
            startPort, endPort
        )
        connection = SinglePipeConnection(
            displayName, startPort, endPort, self
        )
        command = AddSinglePipeConnectionCommand(
            connection, undoNamingHelper, self
        )
        return command

    def _createCreateDoublePipeConnectionCommand(
        self, startPort: DoublePipePortItem, endPort: DoublePipePortItem
    ) -> AddDoublePipeConnectionCommand:
        displayName, undoNamingHelper = self._createDisplayAndUndoNamingHelper(
            startPort, endPort
        )
        connection = DoublePipeConnection(
            displayName, startPort, endPort, self
        )
        command = AddDoublePipeConnectionCommand(
            connection, undoNamingHelper, self
        )
        return command

    def _createDisplayAndUndoNamingHelper(
        self, startPort: PortItemBase, endPort: PortItemBase
    ) -> _tp.Tuple[str, _nu.UndoNamingHelper]:
        createNamingHelper = _nc.CreateNamingHelper(self.namesManager)
        undoNamingHelper = _nu.UndoNamingHelper(
            self.namesManager, createNamingHelper
        )
        displayName = _cnames.generateDefaultConnectionName(
            startPort, endPort, createNamingHelper
        )
        return displayName, undoNamingHelper

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

        distance = _math.sqrt(
            (mousePosition.x() - portItemX) ** 2
            + (mousePosition.y() - portItemY) ** 2
        )
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
        relevantPortItems = self._getRelevantHitPortItems(
            mousePosition, fromPort
        )
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
        _werrs.showMessageBox(errorMessage, title="Not implemented")

    def _getRelevantHitPortItems(
        self, mousePosition: _qtc.QPointF, fromPort: PortItemBase
    ) -> _tp.Sequence[PortItemBase]:
        hitItems = self.diagramScene.items(mousePosition)
        relevantPortItems = [
            i
            for i in hitItems
            if isinstance(i, PortItemBase)
            and type(i) == type(fromPort)
            and not i.connectionList
        ]
        return relevantPortItems

    def exportHydraulics(
        self, exportTo=_tp.Literal["ddck", "mfs"], disableFileExistMsgb=False
    ):
        assert exportTo in ["ddck", "mfs"]

        if not self.isHydraulicConnected():
            messageBox = _qtw.QMessageBox()
            messageBox.setWindowTitle("Hydraulic not connected")
            messageBox.setText(
                "You need to connect all port items before you can export the hydraulics."
            )
            messageBox.setStandardButtons(_qtw.QMessageBox.Ok)
            messageBox.exec()
            return

        self.logger.info(
            "------------------------> START OF EXPORT <------------------------"
        )

        self.sortTrnsysObj()

        fullExportText = ""

        ddckFolder = os.path.join(self.projectFolder, "ddck")

        if exportTo == "mfs":
            mfsFileName = self.diagramName.rsplit(".", 1)[0] + "_mfs.dck"
            exportPath = os.path.join(self.projectFolder, mfsFileName)
        elif exportTo == "ddck":
            exportPath = os.path.join(
                ddckFolder, "hydraulic", "hydraulic.ddck"
            )

        if not disableFileExistMsgb and self._doesFileExistAndDontOverwrite(
            exportPath,
        ):
            return

        self.logger.info("Printing the TRNSYS file...")

        if exportTo == "mfs":
            header = open(
                os.path.join(ddckFolder, "generic", "head.ddck"),
                "r",
                encoding="windows-1252",
            )
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
                o
                for o in self.trnsysObj
                if isinstance(o, SinglePipeConnection) and o.shallBeSimulated
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
                o
                for o in self.trnsysObj
                if isinstance(o, DoublePipeConnection) and o.shallBeSimulated
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

        blackBoxProblem, blackBoxText = exporter.exportBlackBox(
            exportTo=exportTo
        )
        if blackBoxProblem:
            return None

        fullExportText += blackBoxText
        if exportTo == "mfs":
            fullExportText += exporter.exportMassFlows()
            fullExportText += exporter.exportDivSetting(simulationUnit - 10)

        fullExportText += exporter.exportSinglePipeParameters()
        fullExportText += exporter.exportDoublePipeParameters(
            exportTo=exportTo
        )

        fullExportText += exporter.exportParametersFlowSolver(
            simulationUnit, simulationType, descConnLength
        )

        fullExportText += exporter.exportInputsFlowSolver()
        fullExportText += exporter.exportOutputsFlowSolver(simulationUnit)
        fullExportText += exporter.exportFluids() + "\n"
        fullExportText += exporter.exportHydraulicLoops() + "\n"
        fullExportText += exporter.exportPipeAndTeeTypesForTemp(
            simulationUnit + 1
        )  # DC-ERROR
        fullExportText += exporter.exportSinglePipeEnergyBalanceVariables()
        fullExportText += exporter.exportDoublePipeEnergyBalanceVariables()

        fullExportText += exporter.exportMassFlowPrinter(
            self.printerUnitnr, 15
        )
        fullExportText += exporter.exportTempPrinter(
            self.printerUnitnr + 1, 15
        )

        if exportTo == "mfs":
            fullExportText += """\
CONSTANTS 2
TRoomStore=1
Tcw=1
"""
            fullExportText += "ENDS"

        self.logger.info(
            "------------------------> END OF EXPORT <------------------------"
        )

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
            lines = _du.loadDeck(
                exportPath, eraseBeginComment=True, eliminateComments=True
            )
            _du.checkEquationsAndConstants(lines, exportPath)
        except Exception as error:
            errorMessage = f"An error occurred while exporting the system hydraulics: {error}"
            _werrs.showMessageBox(errorMessage)
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
        massFlowContributors = [
            o for o in self.trnsysObj if isinstance(o, _ip.HasInternalPiping)
        ]
        return massFlowContributors

    def isHydraulicConnected(self) -> bool:
        for obj in self.trnsysObj:
            if not isinstance(obj, _ip.HasInternalPiping):
                continue

            internalPiping = obj.getInternalPiping()

            for (
                portItem
            ) in internalPiping.modelPortItemsToGraphicalPortItem.values():
                if not portItem.connectionList:
                    return False

        return True

    def _doesFileExistAndDontOverwrite(self, folderPath):
        if not _pl.Path(folderPath).exists() or self.forceOverwrite:
            return False

        qmb = _qtw.QMessageBox(self)
        qmb.setText(
            f"Warning: {folderPath} already exists. Do you want to overwrite it or cancel?"
        )
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
        self.logger.info(
            "------------------------> START OF EXPORT <------------------------"
        )

        self.sortTrnsysObj()

        fullExportText = ""

        ddckFolder = os.path.join(self.projectFolder, "ddck")

        hydCtrlPath = os.path.join(ddckFolder, "user_control", "user_control_default.ddck")
        if _pl.Path(hydCtrlPath).exists():
            qmb = _qtw.QMessageBox(self)
            qmb.setText(
                "Warning: "
                + "The file user_control_defalut.ddck already exists in the user_control folder. Do you want to overwrite it or cancel?"
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
        fullExportText += "**BEGIN user_control_default.ddck\n"
        fullExportText += "*************************************\n"

        simulationUnit = 450

        exporter = self._createExporter()

        fullExportText += exporter.exportMassFlows()
        fullExportText += exporter.exportDivSetting(simulationUnit - 10)

        self.logger.info(
            "------------------------> END OF EXPORT <------------------------"
        )

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

    def exportPumpConsumptionFile(self):
        self.logger.info("------------------------> START OF EXPORT <------------------------")

        self.sortTrnsysObj()

        fullExportText = ""

        ddckFolder = os.path.join(self.projectFolder, "ddck")

        hydCtrlPath = os.path.join(ddckFolder, "user_control", "pump_consumption_default.ddck")
        if _pl.Path(hydCtrlPath).exists():
            qmb = _qtw.QMessageBox(self)
            qmb.setText(
                "Warning: "
                + "The file pump_consumption_default.ddck already exists in the user_control folder. Do you want to overwrite it or cancel?"
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


        fullExportText = """
**************************************
**BEGIN pump_consumption_default.ddck
**************************************

*****************************
** Author:  exported by GUI
************************************

***************************************************************************
** Description: electrical consumption of circulation pumps
** Source: no type(s) used
** The nominal mass flow rates are taken from GUI,if not precise adapt here
****************************************************************************
"""

        exporter = self._createExporter()

        fullExportText += exporter.exportPumpConsumption()
        fullExportText += """
**************************************
**END pump_consumption_default.ddck
**************************************
"""

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
            self.logger.debug(
                "s has tr id "
                + str(s.trnsysId)
                + " has dname "
                + s.displayName
            )

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
                trnsysObject.deleteConnection()
            else:
                raise AssertionError(
                    f"Don't know how to delete {trnsysObject}."
                )

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
            json.dump(
                self, jsonfile, indent=4, sort_keys=True, cls=_enc.Encoder
            )

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
                        self.logger.debug(
                            "Found the id dict while loading, not setting the ids"
                        )

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
        blockFolderNames.append("user_control")

        ddckFolder = os.path.join(self.projectFolder, "ddck")
        ddckFolders = os.listdir(ddckFolder)
        additionalFolders = []

        for folder in ddckFolders:
            if folder not in blockFolderNames and "StorageTank" not in folder:
                additionalFolders.append(folder)

        if len(additionalFolders) > 0:
            if len(additionalFolders) == 1:
                message = "The following ddck folder does not have a corresponding component in the diagram:"
            else:
                message = "The following ddck folders do not have a corresponding component in the diagram:"

            for folder in additionalFolders:
                message += "\n\t" + folder

            _qtw.QMessageBox.warning(None, "Orphaned ddck folders", message)

        for t in self.trnsysObj:
            t.assignIDsToUninitializedValuesAfterJsonFormatMigration(
                self.idGen
            )

            if hasattr(t, "isTempering"):
                self.logger.debug("tv has " + str(t.isTempering))

        self._decodeHydraulicLoops(blocklist)

        self._setHydraulicLoopsOnStorageTanks()

    def _decodeHydraulicLoops(self, blocklist) -> None:
        singlePipeConnections = [
            c
            for c in self.connectionList
            if isinstance(c, SinglePipeConnection)
        ]
        if "hydraulicLoops" not in blocklist:
            hydraulicLoops = _hlmig.createLoops(
                singlePipeConnections, self.fluids.WATER
            )
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

    # Saving related
    def saveProject(self, showWarning=True):
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
            qmb.setText(
                "Warning: "
                + "This diagram name exists already. Do you want to overwrite or cancel?"
            )
            qmb.setStandardButtons(
                _qtw.QMessageBox.Save | _qtw.QMessageBox.Cancel
            )
            qmb.setDefaultButton(_qtw.QMessageBox.Cancel)
            ret = qmb.exec()

            if ret != _qtw.QMessageBox.Save:
                self.logger.info("Canceling")
                return

            self.logger.info("Overwriting")
            self.encodeDiagram(diagramPath)

        self.encodeDiagram(diagramPath)
        RecentProjectsHandler.addProject(_pl.Path(diagramPath))
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
                    self,
                    "Warning",
                    "This diagram name exists already in the directory."
                    " Please rename this diagram",
                )
            else:
                self.saveAsPath = _pl.Path(
                    self.saveAsPath.stem[
                        0 : self.saveAsPath.name.index(self.diagramName)
                    ]
                    + newName
                )

        self.diagramName = newName
        self.parent().currentFile = newName

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
                t.updateSegmentGradients()

    # Dialog calls
    def showBlockDlg(self, blockItem: BlockItem) -> None:
        renameHelper = self._createRenameHelper()
        dialog = BlockDlg(blockItem, renameHelper, self.projectFolder)
        dialog.exec()

    def showDoublePipeBlockDlg(
        self, connector: _dctor.DoublePipeConnectorBase
    ) -> None:
        renameHelper = self._createRenameHelper()
        dialog = DoublePipeBlockDlg(
            connector, renameHelper, self.projectFolder
        )
        dialog.exec()

    def showDiagramDlg(self):
        c = diagramDlg(self)

    def showGenericPortPairDlg(self, bl):
        c = GenericPortPairDlg(bl, self)

    def showHxDlg(self, hx):
        c = hxDlg(hx, self)

    def showSegmentDlg(self, segmentItem: _sib.SegmentItemBase) -> None:
        renameHelper = self._createRenameHelper()
        segmentDialog = SegmentDialog(segmentItem.connection, renameHelper)
        segmentDialog.exec()

    def showTVentilDlg(self, valve: TVentil) -> None:
        renameHelper = self._createRenameHelper()
        valveDialog = TVentilDlg(valve, renameHelper, self.projectFolder)
        valveDialog.exec()

    def showConfigStorageDlg(self, storageTank: _stwidget.StorageTank) -> None:
        renameHelper = self._createRenameHelper()
        storageDialog = ConfigureStorageDialog(
            storageTank, self, renameHelper, self.projectFolder
        )
        storageDialog.exec()

    def _createRenameHelper(self) -> _rename.RenameHelper:
        renameHelper = _rename.RenameHelper(self.namesManager)
        return renameHelper

    def createProjectFolder(self):
        if not os.path.exists(self.projectFolder):
            os.makedirs(self.projectFolder)

    def copyGenericFolder(self, loadPath):
        genericFolderPath = _pl.Path(loadPath) / "ddck" / "generic"

        if not genericFolderPath.exists():
            self.logger.info("Creating %s", genericFolderPath)
            genericFolderPath.mkdir(parents=True)

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

    @staticmethod
    def createHydraulicDir(projectFolder):
        hydraulicFolder = os.path.join(projectFolder, "ddck", "hydraulic")

        if not os.path.exists(hydraulicFolder):
            os.makedirs(hydraulicFolder)

    def createWeatherAndControlDirs(self, projectFolder):

        ddckFolder = os.path.join(projectFolder, "ddck")
        weatherFolder = os.path.join(ddckFolder, "weather")
        controlFolder = os.path.join(ddckFolder, "user_control")

        if not os.path.exists(weatherFolder):
            self.logger.info("Creating " + weatherFolder)
            os.makedirs(weatherFolder)

        if not os.path.exists(controlFolder):
            self.logger.info("Creating " + controlFolder)
            os.makedirs(controlFolder)

    def editHydraulicLoop(self, singlePipeConnection: SinglePipeConnection):
        assert isinstance(singlePipeConnection.fromPort, SinglePipePortItem)

        hydraulicLoop = self.hydraulicLoops.getLoopForExistingConnection(
            singlePipeConnection
        )
        _hledit.edit(hydraulicLoop, self.hydraulicLoops, self.fluids)

        self._updateGradientsInHydraulicLoop(hydraulicLoop)

    @staticmethod
    def _updateGradientsInHydraulicLoop(
        hydraulicLoop: _hlm.HydraulicLoop,
    ) -> None:
        for connection in hydraulicLoop.connections:
            connection.updateSegmentGradients()

    @_tp.override
    def getInternalPipings(self) -> _cabc.Sequence[_ip.HasInternalPiping]:
        return [
            o for o in self.trnsysObj if isinstance(o, _ip.HasInternalPiping)
        ]

    def toggleSnap(self) -> None:
        self.snapGrid = not self.snapGrid
        self.diagramScene.update()
