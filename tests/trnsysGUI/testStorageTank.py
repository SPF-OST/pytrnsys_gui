import json as _json
import logging as _log
import unittest.mock as _mock
import cgitb as _cgitb

from PyQt5 import QtWidgets as _widgets

import trnsysGUI.StorageTank as _st


# Sometimes PyQT crashes only returning with quite a cryptic error code. Sometimes, again, we can get
# a more helpful stack trace using the cgitb module.
_cgitb.enable(format="text")


class TestStorageTank:
    def testSerialization(self, tmp_path):
        storageTankJson = """{
    ".__BlockDict__": true,
    "BlockDisplayName": "Dhw",
    "BlockName": "StorageTank",
    "FlippedH": false,
    "FlippedV": false,
    "GroupName": "defaultGroup",
    "HxList": [
        {
            "DisplayName": "SolarHx",
            "Height": 40.0,
            "ID": 1976,
            "Offset": [
                0.0,
                154.0
            ],
            "ParentID": 1975,
            "Port1ID": 1977,
            "Port2ID": 1978,
            "SideNr": 0,
            "Width": 40,
            "connTrnsysID": 639
        }
    ],
    "ID": 1975,
    "PortPairList": [
        {
            "ConnCID": 440,
            "ConnDisName": "TesDHWPortHpDhw",
            "ConnID": 1984,
            "Port1ID": 1982,
            "Port1offset": 11.0,
            "Port2ID": 1983,
            "Port2offset": 142.0,
            "Side": true,
            "trnsysID": 641
        },
        {
            "ConnCID": 881,
            "ConnDisName": "TesDHWPortDhwRecir",
            "ConnID": 3926,
            "Port1ID": 3924,
            "Port1offset": 66.0,
            "Port2ID": 3925,
            "Port2offset": 22.0,
            "Side": false,
            "trnsysID": 1271
        },
        {
            "ConnCID": 886,
            "ConnDisName": "TesDHWPortDHW",
            "ConnID": 3943,
            "Port1ID": 3941,
            "Port1offset": 209.0,
            "Port2ID": 3942,
            "Port2offset": 11.0,
            "Side": false,
            "trnsysID": 1277
        }
    ],
    "StoragePosition": [
        -681.9155092592591,
        -581.1302806712963
    ],
    "size_h": 220.0,
    "trnsysID": 638
}"""

        serializedStorageTank = _json.loads(storageTankJson)

        logger = _log.getLogger("root")

        (
            diagramViewMock,
            *objectsNeededToBeKeptAliveForDurationOfTest,
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, tmp_path)

        storageTank = _st.StorageTank(trnsysType="StorageTank", parent=diagramViewMock)
        diagramViewMock.scene().addItem(storageTank)

        connections = []
        blocks = []
        storageTank.decode(serializedStorageTank, connections, blocks)

        for heatExchanger in storageTank.heatExchangers:
            heatExchanger.initLoad()

        for connection in connections:
            connection.initLoad()

        reserializedStorageTank = storageTank.encode()[1]
        reserializedStorageTankJson = _json.dumps(
            reserializedStorageTank, indent=4, sort_keys=True
        )

        assert reserializedStorageTankJson == storageTankJson

    @staticmethod
    def _createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, tmp_path):
        application = _widgets.QApplication([])

        mainWindow = _widgets.QMainWindow()

        editorMock = _widgets.QWidget(parent=mainWindow)
        editorMock.connectionList = []
        editorMock.logger = logger
        editorMock.trnsysObj = []
        editorMock.groupList = []
        editorMock.projectPath = str(tmp_path)
        editorMock.splitter = _mock.Mock(name="splitter")
        editorMock.idGen = _mock.Mock(
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

        editorMock.idGen.getID = lambda: "my-id"
        editorMock.idGen.getTrnsysID = lambda: "my-trnsys-id"
        editorMock.idGen.getStoragenTes = lambda: "my-storage-tes"
        editorMock.idGen.getStoragenTes = lambda: "my-storage-type"
        editorMock.idGen.getConnID = lambda: "conn-id"

        graphicsScene = _widgets.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = graphicsScene

        diagramViewMock = _widgets.QGraphicsView(graphicsScene, parent=editorMock)
        diagramViewMock.logger = logger

        mainWindow.setCentralWidget(editorMock)
        mainWindow.showMinimized()

        return diagramViewMock, [application, mainWindow, editorMock, graphicsScene]
