import cgitb as _cgitb  # pylint: disable=deprecated-module
import logging as _log
import unittest.mock as _mock
import typing as _tp

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import trnsysGUI.blockItems.getBlockItem as _gbi
from trnsysGUI.AirSourceHP import AirSourceHP
from trnsysGUI.Boiler import Boiler
from trnsysGUI.CentralReceiver import CentralReceiver
from trnsysGUI.Collector import Collector
from trnsysGUI.ExternalHx import ExternalHx
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.GraphicalItem import GraphicalItem  # type: ignore[attr-defined]
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
from trnsysGUI.pumpsAndTaps.tap import Tap
from trnsysGUI.pumpsAndTaps.tapMains import TapMains
from trnsysGUI.connection.connectors.connector import Connector
from trnsysGUI.connection.connectors.doubleDoublePipeConnector import DoubleDoublePipeConnector
from trnsysGUI.connection.connectors.singleDoublePipeConnector import SingleDoublePipeConnector
from trnsysGUI.crystalizer import Crystalizer
from trnsysGUI.geotherm import Geotherm
from trnsysGUI.pumpsAndTaps.pump import Pump
from trnsysGUI.sink import Sink
from trnsysGUI.source import Source
from trnsysGUI.sourceSink import SourceSink
from trnsysGUI.storageTank.widget import StorageTank
from trnsysGUI.teePieces.doublePipeTeePiece import DoublePipeTeePiece
from trnsysGUI.teePieces.teePiece import TeePiece
from trnsysGUI.water import Water

import trnsysGUI.names.manager as _nman

# Sometimes PyQT crashes only returning with quite a cryptic error code. Sometimes, again, we can get
# a more helpful stack trace using the cgitb module.
_cgitb.enable(format="text")

_BLOCK_ITEM_CASES = [
    ("TeePiece", TeePiece, "Tee5"),
    ("DPTee", DoublePipeTeePiece, "DTee5"),
    ("SPCnr", SingleDoublePipeConnector, "SCnr5"),
    ("DPCnr", DoubleDoublePipeConnector, "DCnr5"),
    ("TVentil", TVentil, "Val5"),
    ("Pump", Pump, "Pump5"),
    ("Connector", Connector, "Conn5"),
    ("Crystalizer", Crystalizer, "Cryt5"),
    ("WTap_main", TapMains, "WtSp5"),
    ("Collector", Collector, "Coll5"),
    ("Kollektor", Collector, "Coll5"),
    ("HP", HeatPump, "HP5"),
    ("IceStorage", IceStorage, "IceS5"),
    ("PitStorage", PitStorage, "PitS5"),
    ("Radiator", Radiator, "Rad5"),
    ("WTap", Tap, "WtTp5"),
    ("GenericBlock", GenericBlock, "GBlk5"),
    ("HPTwoHx", HeatPumpTwoHx, "HP5"),
    ("HPDoubleDual", HPDoubleDual, "HPDD5"),
    ("HPDual", HPDual, "HPDS5"),
    ("Boiler", Boiler, "Bolr5"),
    ("AirSourceHP", AirSourceHP, "Ashp5"),
    ("PV", PV, "PV5"),
    ("GroundSourceHx", GroundSourceHx, "Gshx5"),
    ("ExternalHx", ExternalHx, "Hx5"),
    ("IceStorageTwoHx", IceStorageTwoHx, "IceS5"),
    ("Sink", Sink, "QSnk5"),
    ("Source", Source, "QSrc5"),
    ("SourceSink", SourceSink, "QExc5"),
    ("Geotherm", Geotherm, "GeoT5"),
    ("Water", Water, "QWat5"),
    ("powerBlock", SteamPowerBlock, "StPB5"),
    ("CSP_PT", ParabolicTroughField, "PT5"),
    ("CSP_CR", CentralReceiver, "CR5"),
    ("coldSaltTank", SaltTankCold, "ClSt5"),
    ("hotSaltTank", SaltTankHot, "HtSt5"),
]

_BLOCK_ITEM_CASES_WITHOUT_NAME = [(x, y) for x, y, _ in _BLOCK_ITEM_CASES]


class _DummyDdckDirFileOrDirNamesProvider(_nman.AbstractDdckDirFileOrDirNamesProvider):
    def hasFileOrDirName(self, name: str) -> bool:
        return False


class TestGetBlockItem:
    @_pt.mark.parametrize("componentTypeName, componentType, displayName", _BLOCK_ITEM_CASES)
    def testGetNewBlockItem(
        self, componentTypeName, componentType, displayName, tmp_path, qtbot  # pylint: disable=invalid-name  # /NOSONAR
    ) -> None:
        editorMock = self._testHelper(tmp_path, qtbot)
        namesManagerMock = self._createNamesManager()
        blockItem = _gbi.createBlockItem(componentTypeName, editorMock, namesManagerMock, displayName)
        assert isinstance(blockItem, componentType)
        assert blockItem.displayName == displayName

    def testGetNewStorageTank(self, tmp_path, qtbot) -> None:  # pylint: disable=invalid-name  # /NOSONAR
        editorMock = self._testHelper(tmp_path, qtbot)
        namesManagerMock = self._createNamesManager()

        displayName = "Tes"
        blockItem = _gbi.createBlockItem("StorageTank", editorMock, namesManagerMock, displayName)

        assert isinstance(blockItem, StorageTank)
        assert blockItem.displayName == displayName

    def testGetNewGraphicalItem(self, tmp_path, qtbot) -> None:  # pylint: disable=invalid-name  # /NOSONAR
        editorMock = self._testHelper(tmp_path, qtbot)
        namesManagerMock = self._createNamesManager()

        blockItem = _gbi.createBlockItem("GraphicalItem", editorMock, namesManagerMock)
        assert isinstance(blockItem, GraphicalItem)

    def testGetNewUnknownBlockItemRaises(self, tmp_path, qtbot) -> None:  # pylint: disable=invalid-name  # /NOSONAR
        editorMock = self._testHelper(tmp_path, qtbot)

        with _pt.raises(ValueError):
            namesManagerMock = self._createNamesManager()

            _gbi.createBlockItem("Blk", editorMock, namesManagerMock)

    @_pt.mark.parametrize("componentTypeName, componentType", _BLOCK_ITEM_CASES_WITHOUT_NAME)
    def testGetLoadedBlockItem(
        self, componentTypeName, componentType, tmp_path, qtbot  # pylint: disable=invalid-name  # /NOSONAR
    ) -> None:
        editorMock = self._testHelper(tmp_path, qtbot)
        namesManagerMock = self._createNamesManager()

        displayName = f"{componentTypeName}753"
        blockItem = _gbi.createBlockItem(componentTypeName, editorMock, namesManagerMock, displayName)

        assert isinstance(blockItem, componentType)
        assert blockItem.displayName == displayName

    def testGetLoadedStorageTank(self, tmp_path, qtbot) -> None:  # pylint: disable=invalid-name  # /NOSONAR
        editorMock = self._testHelper(tmp_path, qtbot)
        namesManagerMock = self._createNamesManager()

        displayName = "StorageTank753"
        blockItem = _gbi.createBlockItem("StorageTank", editorMock, namesManagerMock, displayName)

        assert isinstance(blockItem, StorageTank)
        assert blockItem.displayName == displayName

    def _testHelper(self, tmp_path, bot):  # pylint: disable=invalid-name  # /NOSONAR
        logger = _log.getLogger("root")
        (
            editorMock,
            [mainWindow, _],
        ) = self._createEditorMock(logger, tmp_path)

        bot.addWidget(mainWindow)

        return editorMock

    @staticmethod
    def _createNamesManager() -> _nman.NamesManager:
        existingNames = []

        expectedDisplayName: str
        for [*_, expectedDisplayName] in _BLOCK_ITEM_CASES:
            baseName = expectedDisplayName[: -len("5")]
            existingNames.append(baseName)
            existingNames.extend(f"{baseName}{i}" for i in range(2, 5))

        ddckDirFileOrDirNamesProvider = _DummyDdckDirFileOrDirNamesProvider()
        namesManager = _nman.NamesManager(existingNames, ddckDirFileOrDirNamesProvider)

        return namesManager

    @staticmethod
    def _createEditorMock(logger, projectFolder):
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
        editorMock.snapGrid = False
        editorMock.alignMode = False

        editorMock.idGen.getID = lambda: 7701
        editorMock.idGen.getTrnsysID = lambda: 7702
        editorMock.idGen.getStoragenTes = lambda: 7703
        editorMock.idGen.getStorageType = lambda: 7704

        editorMock.namesManager = None

        graphicsScene = _qtw.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = graphicsScene
        editorMock.graphicalObj = []

        mainWindow.setCentralWidget(editorMock)
        mainWindow.showMinimized()

        return editorMock, [mainWindow, graphicsScene]
