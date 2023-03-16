import logging as _log
import unittest.mock as _m
import pytest as _pt

from PyQt5 import QtWidgets as _widgets
from PyQt5.QtCore import QPoint

import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.doublePipeSegmentItem as _dpsi
import trnsysGUI.internalPiping as _ip


class TestDoublePipeConnection:
    @_pt.mark.skip("Incomplete tdd style reverse engineering of required mocks")
    def testInitialization(self, qtbot):  # pylint: disable=unused-argument
        logger = _log.getLogger("root")
        (
            editorMock,
            objectsToKeepAlive  # pylint: disable=unused-variable
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, ".")
        fromPort = self._getPortMock("fromPort1")
        toPort = self._getPortMock("toPort1")

        dpSegItem = _m.Mock(spec=_dpsi.DoublePipeSegmentItem)
        with _m.patch("trnsysGUI.connection.doublePipeConnection.DoublePipeConnection._createSegmentItem") as creator:
            creator.return_value = dpSegItem
            _dpc.DoublePipeConnection(fromPort, toPort, editorMock)

    @staticmethod
    def _getPortMock(name):
        portMock = _m.Mock(spec=_dppi.DoublePipePortItem)
        portMock.parent = _ip.HasInternalPiping()
        portMock.parent.displayName = name

        def scenePos():
            return QPoint(5, 6)

        portMock.scenePos = scenePos
        portMock.side = 1
        portMock.name = name
        return portMock

    @staticmethod
    def _createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, projectFolder):
        mainWindow = _widgets.QStackedWidget()

        editorMock = _widgets.QWidget(parent=mainWindow)
        editorMock.connectionList = []
        editorMock.logger = logger
        editorMock.trnsysObj = []
        editorMock.projectFolder = str(projectFolder)
        editorMock.splitter = _m.Mock(name="splitter")
        editorMock.idGen = _m.Mock(
            name="idGen",
            spec_set=[
                "getID",
                "getTrnsysID",
                "getStoragenTes",
                "getStorageType",
                "getConnID",
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
        editorMock.idGen.getConnID = lambda: 7705

        graphicsScene = _widgets.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = _m.Mock(name="diagramScene")

        def addItem(_):  # pylint: disable=unused-argument
            pass

        editorMock.diagramScene.addItem = addItem

        def items():
            return []

        editorMock.diagramScene.items = items
        mainWindow.showMinimized()

        return editorMock, [mainWindow, graphicsScene]
