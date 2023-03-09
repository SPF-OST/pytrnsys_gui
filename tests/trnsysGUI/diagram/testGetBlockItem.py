import cgitb as _cgitb
import logging as _log
import unittest.mock as _mock
import pytest as _pt

import PyQt5.QtWidgets as _qtw

import trnsysGUI.diagram.getBlockItem as _gbi

from trnsysGUI.AirSourceHP import AirSourceHP
from trnsysGUI.Boiler import Boiler
from trnsysGUI.CentralReceiver import CentralReceiver
from trnsysGUI.Collector import Collector
from trnsysGUI.ExternalHx import ExternalHx
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.Graphicaltem import GraphicalItem  # type: ignore[attr-defined]
from trnsysGUI.GroundSourceHx import GroundSourceHx
from trnsysGUI.HPDoubleDual import HPDoubleDual
from trnsysGUI.HPDual import HPDual
from trnsysGUI.HeatPump import HeatPump
from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx
from trnsysGUI.IceStorage import IceStorage
from trnsysGUI.IceStorageTwoHx import IceStorageTwoHx
from trnsysGUI.PV import PV
from trnsysGUI.ParabolicTroughField import ParabolicTroughField
from trnsysGUI.PitStorage import PitStorage
from trnsysGUI.Radiator import Radiator
from trnsysGUI.SaltTankCold import SaltTankCold
from trnsysGUI.SaltTankHot import SaltTankHot
from trnsysGUI.SteamPowerBlock import SteamPowerBlock
from trnsysGUI.TVentil import TVentil
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.WTap import WTap
from trnsysGUI.WTap_main import WTap_main
from trnsysGUI.connectors.connector import Connector
from trnsysGUI.connectors.doubleDoublePipeConnector import DoubleDoublePipeConnector
from trnsysGUI.connectors.singleDoublePipeConnector import SingleDoublePipeConnector
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.pump import Pump
from trnsysGUI.sink import Sink
from trnsysGUI.source import Source
from trnsysGUI.sourceSink import SourceSink
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.water import Water

# Sometimes PyQT crashes only returning with quite a cryptic error code. Sometimes, again, we can get
# a more helpful stack trace using the cgitb module.
_cgitb.enable(format="text")

_BLOCKITEMCASESWITHPROJECTPATH = [
    ("TeePiece", TeePiece, "Tee7701"),
    ("DPTee", DoublePipeTeePiece, "DTee7701"),
    ("SPCnr", SingleDoublePipeConnector, "SCnr7701"),
    ("DPCnr", DoubleDoublePipeConnector, "DCnr7701"),
    ("TVentil", TVentil, "Val7701"),
    ("Pump", Pump, "Pump7701"),
    ("Connector", Connector, "Conn7701"),
    ("Crystalizer", Crystalizer, "Cryt7701"),
    ("WTap_main", WTap_main, "WtSp7701"),
]

res, _ = zip(_BLOCKITEMCASESWITHPROJECTPATH)

_BLOCKITEMCASESWITHPROJECTFOLDER = [
    ("Collector", Collector),
    ("HP", HeatPump),
    ("IceStorage", IceStorage),
    ("PitStorage", PitStorage),
    ("Radiator", Radiator),
    ("WTap", WTap),
    ("GenericBlock", GenericBlock),
    ("HPTwoHx", HeatPumpTwoHx),
    ("HPDoubleDual", HPDoubleDual),
    ("HPDual", HPDual),
    ("Boiler", Boiler),
    ("AirSourceHP", AirSourceHP),
    ("PV", PV),
    ("GroundSourceHx", GroundSourceHx),
    ("ExternalHx", ExternalHx),
    ("IceStorageTwoHx", IceStorageTwoHx),
    ("Sink", Sink),
    ("Source", Source),
    ("SourceSink", SourceSink),
    ("Geotherm", Geotherm),
    ("Water", Water),
    ("powerBlock", SteamPowerBlock),
    ("CSP_PT", ParabolicTroughField),
    ("CSP_CR", CentralReceiver),
    ("coldSaltTank", SaltTankCold),
    ("hotSaltTank", SaltTankHot),
]


class TestGetBlockItem:

    @_pt.mark.parametrize("componentType, blockItemType, displayName", _BLOCKITEMCASESWITHPROJECTPATH)
    def testGetBlockItem(self, componentType, blockItemType, displayName, tmp_path,  # pylint: disable=invalid-name
                         request: _pt.FixtureRequest) -> None:
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem(componentType, editorMock)
        assert isinstance(blockItem, blockItemType)
        assert blockItem.displayName == displayName

    @_pt.mark.parametrize("componentType, blockItemType", _BLOCKITEMCASESWITHPROJECTFOLDER)
    def testGetBlockItemWithProjectFolder(self, componentType, blockItemType, tmp_path,  # pylint: disable=invalid-name
                                          request: _pt.FixtureRequest) -> None:
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem(componentType, editorMock)
        assert isinstance(blockItem, blockItemType)

    def testGetBlockItemStorageTank(self, tmp_path,
                                    request: _pt.FixtureRequest) -> None:  # pylint: disable=invalid-name
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem("StorageTank", editorMock)
        assert isinstance(blockItem, StorageTank)
        assert blockItem.displayName == "Tes7701"

    def testGetGraphicalItem(self, tmp_path,
                             request: _pt.FixtureRequest) -> None:  # pylint: disable=invalid-name
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem("GraphicalItem", editorMock)
        assert isinstance(blockItem, GraphicalItem)

    def testGetBlockItemRaises(self) -> None:
        with _pt.raises(AssertionError):
            _gbi.getBlockItem("Blk", 0)

    @_pt.mark.parametrize("componentType, blockItemType", _BLOCKITEMCASESWITHPROJECTPATH[:][0:2])
    def testGetLoaded(self, componentType, blockItemType, tmp_path,
                      request: _pt.FixtureRequest) -> None:  # pylint: disable=invalid-name
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem(componentType, editorMock, displayName=componentType, loadedBlock=True)
        assert isinstance(blockItem, blockItemType)
        assert blockItem.displayName == componentType

    @_pt.mark.parametrize("componentType, blockItemType", _BLOCKITEMCASESWITHPROJECTFOLDER)
    def testGetLoadedWithProjectFolder(self, componentType, blockItemType, tmp_path,
                      request: _pt.FixtureRequest) -> None:  # pylint: disable=invalid-name
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem(componentType, editorMock, displayName=componentType, loadedBlock=True)
        assert isinstance(blockItem, blockItemType)
        assert blockItem.displayName == componentType

    def testGetLoadedStorageTank(self, tmp_path, request: _pt.FixtureRequest) -> None:  # pylint: disable=invalid-name
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem("StorageTank", editorMock, displayName="StorageTank", loadedBlock=True)
        assert isinstance(blockItem, StorageTank)
        assert blockItem.displayName == "StorageTank"

    def testGetLoadedGraphicalItem(self, tmp_path, request: _pt.FixtureRequest) -> None:  # pylint: disable=invalid-name
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem("GraphicalItem", editorMock, loadedGI=True)
        assert isinstance(blockItem, GraphicalItem)

    def _testHelper(self, tmp_path, request):
        logger = _log.getLogger("root")
        (
            editorMock,
            [application, mainWindow, graphicsScene],  # pylint: disable=unused-variable
        ) = self._createEditorMock(logger, tmp_path)

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)
        return editorMock

    @staticmethod
    def _createEditorMock(logger, projectPath):
        application = _qtw.QApplication([])

        mainWindow = _qtw.QMainWindow()

        editorMock = _qtw.QWidget(parent=mainWindow)
        editorMock.connectionList = []
        editorMock.logger = logger
        editorMock.trnsysObj = []
        editorMock.projectPath = str(projectPath)
        editorMock.projectFolder = str(projectPath)
        editorMock.splitter = _mock.Mock(name="splitter")
        editorMock.idGen = _mock.Mock(
            name="idGen",
            spec_set=[
                "getID",
                "getTrnsysID",
                "getStoragenTes",
                "getStorageType",
            ],
        )
        editorMock.moveDirectPorts = True
        editorMock.editorMode = 1
        editorMock.snapGrid = False
        editorMock.alignMode = False

        editorMock.idGen.getID = lambda: 7701
        editorMock.idGen.getTrnsysID = lambda: 7702
        editorMock.idGen.getStoragenTes = lambda: 7703
        editorMock.idGen.getStorageType = lambda: 7704

        graphicsScene = _qtw.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = graphicsScene
        editorMock.graphicalObj = []

        mainWindow.setCentralWidget(editorMock)
        mainWindow.showMinimized()

        return editorMock, [application, mainWindow, graphicsScene]
