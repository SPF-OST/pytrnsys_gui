import cgitb as _cgitb
import logging as _log
import pytest as _pt
import unittest.mock as _mock

import PyQt5.QtWidgets as _qtw

from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.diagram.view import View as _v

from trnsysGUI.AirSourceHP import AirSourceHP
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.Boiler import Boiler
from trnsysGUI.CentralReceiver import CentralReceiver
from trnsysGUI.Collector import Collector
from trnsysGUI.Control import Control
from trnsysGUI.ExternalHx import ExternalHx
from trnsysGUI.GenericBlock import GenericBlock
from trnsysGUI.Graphicaltem import GraphicalItem
from trnsysGUI.GroundSourceHx import GroundSourceHx
from trnsysGUI.HPDoubleDual import HPDoubleDual
from trnsysGUI.HPDual import HPDual
from trnsysGUI.HeatPump import HeatPump
from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx
from trnsysGUI.IceStorage import IceStorage
from trnsysGUI.IceStorageTwoHx import IceStorageTwoHx
from trnsysGUI.MasterControl import MasterControl
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
from trnsysGUI.deleteBlockCommand import DeleteBlockCommand
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
    ("TeePiece", TeePiece),
    ("DPTee", DoublePipeTeePiece),
    ("SPCnr", SingleDoublePipeConnector),
    ("DPCnr", DoubleDoublePipeConnector),
    ("TVentil", TVentil),
    ("Pump", Pump),
    ("Connector", Connector),
    ("GraphicalItem", GraphicalItem),
    ("Crystalizer", Crystalizer),
    ("WTap_main", WTap_main),
]

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

# todo: the following cases likely expose a bug in the code
_BLOCKITEMCASESWITHDISPLAYNAME = [
    ("MasterControl", MasterControl),
    ("Control", Control),
]


# ("StorageTank", StorageTank),

class TestView:
    # def setup(self):
    #     self.editor = self._createEditor('.')

    @_pt.mark.parametrize("componentType, blockItemType", _BLOCKITEMCASESWITHPROJECTPATH)
    def testGetBlockItem(self, componentType, blockItemType, tmp_path, request: _pt.FixtureRequest) -> None:
        logger = _log.getLogger("root")
        (
            editorMock,
            [application, mainWindow, graphicsScene],  # pylint: disable=unused-variable
        ) = self._createEditorMock(logger, tmp_path)

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        blockItem = _v._getBlockItem(componentType, editorMock)
        assert isinstance(blockItem, blockItemType)

    @_pt.mark.parametrize("componentType, blockItemType", _BLOCKITEMCASESWITHPROJECTFOLDER)
    def testGetBlockItemWithProjectFolder(self, componentType, blockItemType, tmp_path,
                                          request: _pt.FixtureRequest) -> None:
        logger = _log.getLogger("root")
        (
            editorMock,
            [application, mainWindow, graphicsScene],  # pylint: disable=unused-variable
        ) = self._createEditorMock(logger, tmp_path)

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        blockItem = _v._getBlockItem(componentType, editorMock)
        assert isinstance(blockItem, blockItemType)

    @_pt.mark.parametrize("componentType, blockItemType", _BLOCKITEMCASESWITHDISPLAYNAME)
    def testGetBlockItemSpecial(self, componentType, blockItemType, tmp_path,
                                request: _pt.FixtureRequest) -> None:
        logger = _log.getLogger("root")
        (
            editorMock,
            [application, mainWindow, graphicsScene],  # pylint: disable=unused-variable
        ) = self._createEditorMock(logger, tmp_path)

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        blockItem = _v._getBlockItem(componentType, editorMock)
        assert isinstance(blockItem, blockItemType)

    def testGetBlockItemRaises(self, tmp_path, request: _pt.FixtureRequest) -> None:
        logger = _log.getLogger("root")
        (
            editorMock,
            [application, mainWindow, graphicsScene],  # pylint: disable=unused-variable
        ) = self._createEditorMock(logger, tmp_path)

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)
        with _pt.raises(AssertionError) as e:
            _v._getBlockItem("Blk", editorMock)

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
            ],
        )
        editorMock.moveDirectPorts = True
        editorMock.editorMode = 1
        editorMock.snapGrid = False
        editorMock.alignMode = False

        editorMock.idGen.getID = lambda: 7701
        editorMock.idGen.getTrnsysID = lambda: 7702

        graphicsScene = _qtw.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = graphicsScene
        editorMock.graphicalObj = []

        mainWindow.setCentralWidget(editorMock)
        mainWindow.showMinimized()

        return editorMock, [application, mainWindow, graphicsScene]
