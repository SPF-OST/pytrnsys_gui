import cgitb as _cgitb
import logging as _log
import unittest.mock as _mock
import pytest as _pt

import PyQt5.QtWidgets as _qtw

import trnsysGUI.blockItems.getBlockItem as _gbi

from trnsysGUI.AirSourceHP import AirSourceHP
from trnsysGUI.Boiler import Boiler
from trnsysGUI.CentralReceiver import CentralReceiver
from trnsysGUI.Collector import Collector
from trnsysGUI.connectors.connector import Connector
from trnsysGUI.connectors.doubleDoublePipeConnector import DoubleDoublePipeConnector
from trnsysGUI.connectors.singleDoublePipeConnector import SingleDoublePipeConnector
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.ExternalHx import ExternalHx
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.GraphicalItem import GraphicalItem  # type: ignore[attr-defined]
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.GroundSourceHx import GroundSourceHx
from trnsysGUI.HPDoubleDual import HPDoubleDual
from trnsysGUI.HPDual import HPDual
from trnsysGUI.HeatPump import HeatPump
from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx
from trnsysGUI.IceStorage import IceStorage
from trnsysGUI.IceStorageTwoHx import IceStorageTwoHx
from trnsysGUI.ParabolicTroughField import ParabolicTroughField
from trnsysGUI.PitStorage import PitStorage
from trnsysGUI.pump import Pump
from trnsysGUI.PV import PV
from trnsysGUI.Radiator import Radiator
from trnsysGUI.SaltTankCold import SaltTankCold
from trnsysGUI.SaltTankHot import SaltTankHot
from trnsysGUI.sink import Sink
from trnsysGUI.source import Source
from trnsysGUI.sourceSink import SourceSink
from trnsysGUI.SteamPowerBlock import SteamPowerBlock
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.TVentil import TVentil
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.water import Water
from trnsysGUI.WTap import WTap
from trnsysGUI.WTap_main import WTap_main

# Sometimes PyQT crashes only returning with quite a cryptic error code. Sometimes, again, we can get
# a more helpful stack trace using the cgitb module.
_cgitb.enable(format="text")

_BLOCK_ITEM_CASES = [
    ("TeePiece", TeePiece, "Tee7701"),
    ("DPTee", DoublePipeTeePiece, "DTee7701"),
    ("SPCnr", SingleDoublePipeConnector, "SCnr7701"),
    ("DPCnr", DoubleDoublePipeConnector, "DCnr7701"),
    ("TVentil", TVentil, "Val7701"),
    ("Pump", Pump, "Pump7701"),
    ("Connector", Connector, "Conn7701"),
    ("Crystalizer", Crystalizer, "Cryt7701"),
    ("WTap_main", WTap_main, "WtSp7701"),
    ("Collector", Collector, "Coll7701"),
    ("Kollektor", Collector, "Coll7701"),
    ("HP", HeatPump, "HP7701"),
    ("IceStorage", IceStorage, "IceS7701"),
    ("PitStorage", PitStorage, "PitS7701"),
    ("Radiator", Radiator, "Rad7701"),
    ("WTap", WTap, "WtTp7701"),
    ("GenericBlock", GenericBlock, "GBlk7701"),
    ("HPTwoHx", HeatPumpTwoHx, "HP7701"),
    ("HPDoubleDual", HPDoubleDual, "HPDD7701"),
    ("HPDual", HPDual, "HPDS7701"),
    ("Boiler", Boiler, "Bolr7701"),
    ("AirSourceHP", AirSourceHP, "Ashp7701"),
    ("PV", PV, "PV7701"),
    ("GroundSourceHx", GroundSourceHx, "Gshx7701"),
    ("ExternalHx", ExternalHx, "Hx7701"),
    ("IceStorageTwoHx", IceStorageTwoHx, "IceS7701"),
    ("Sink", Sink, "QSnk7701"),
    ("Source", Source, "QSrc7701"),
    ("SourceSink", SourceSink, "QExc7701"),
    ("Geotherm", Geotherm, "GeoT7701"),
    ("Water", Water, "QWat7701"),
    ("powerBlock", SteamPowerBlock, "StPB7701"),
    ("CSP_PT", ParabolicTroughField, "PT7701"),
    ("CSP_CR", CentralReceiver, "CR7701"),
    ("coldSaltTank", SaltTankCold, "ClSt7701"),
    ("hotSaltTank", SaltTankHot, "HtSt7701"),
]

_BLOCK_ITEM_CASES_WITHOUT_NAME = [(x, y) for x, y, _ in _BLOCK_ITEM_CASES]


class TestGetBlockItem:
    @_pt.mark.parametrize("componentTypeName, componentType, displayName", _BLOCK_ITEM_CASES)
    def testGetNewBlockItem(
        self,
        componentTypeName,
        componentType,
        displayName,
        tmp_path,  # pylint: disable=invalid-name  # /NOSONAR
        request: _pt.FixtureRequest,
    ) -> None:
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem(componentTypeName, editorMock)
        assert isinstance(blockItem, componentType)
        assert blockItem.displayName == displayName

    def testGetNewStorageTank(
        self, tmp_path, request: _pt.FixtureRequest  # pylint: disable=invalid-name  # /NOSONAR
    ) -> None:
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem("StorageTank", editorMock)
        assert isinstance(blockItem, StorageTank)
        assert blockItem.displayName == "Tes7701"

    def testGetNewGraphicalItem(
        self, tmp_path, request: _pt.FixtureRequest  # pylint: disable=invalid-name  # /NOSONAR
    ) -> None:
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem("GraphicalItem", editorMock)
        assert isinstance(blockItem, GraphicalItem)

    def testGetNewUnknownBlockItemRaises(
        self, tmp_path, request: _pt.FixtureRequest  # pylint: disable=invalid-name  # /NOSONAR
    ) -> None:
        editorMock = self._testHelper(tmp_path, request)

        with _pt.raises(ValueError):
            _gbi.getBlockItem("Blk", editorMock)

    @_pt.mark.parametrize("componentTypeName, componentType", _BLOCK_ITEM_CASES_WITHOUT_NAME)
    def testGetLoadedBlockItem(
        self,
        componentTypeName,
        componentType,
        tmp_path,  # pylint: disable=invalid-name  # /NOSONAR
        request: _pt.FixtureRequest,
    ) -> None:
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem(componentTypeName, editorMock, displayName=componentTypeName)
        assert isinstance(blockItem, componentType)
        assert blockItem.displayName == componentTypeName

    def testGetLoadedStorageTank(
        self, tmp_path, request: _pt.FixtureRequest  # pylint: disable=invalid-name  # /NOSONAR
    ) -> None:
        editorMock = self._testHelper(tmp_path, request)
        blockItem = _gbi.getBlockItem("StorageTank", editorMock, displayName="StorageTank")
        assert isinstance(blockItem, StorageTank)
        assert blockItem.displayName == "StorageTank"

    def _testHelper(self, tmp_path, request):  # pylint: disable=invalid-name  # /NOSONAR
        logger = _log.getLogger("root")
        (
            editorMock,
            [application, _, _],
        ) = self._createEditorMock(logger, tmp_path)

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)
        return editorMock

    @staticmethod
    def _createEditorMock(logger, projectFolder):
        application = _qtw.QApplication([])

        mainWindow = _qtw.QMainWindow()

        editorMock = _qtw.QWidget(parent=mainWindow)
        editorMock.connectionList = []
        editorMock.logger = logger
        editorMock.trnsysObj = []
        editorMock.projectFolder = str(projectFolder)
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