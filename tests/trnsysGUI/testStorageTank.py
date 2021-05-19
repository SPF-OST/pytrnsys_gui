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
        storageTankLegacyJson = """{
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
        expectedStorageTankJson = """{
    ".__BlockDict__": true,
    "BlockDisplayName": "Dhw",
    "BlockName": "StorageTank",
    "__version__": "05f422d3-41fd-48d1-b8d0-4655d9f65247",
    "directPortPairs": [
        {
            "connectionId": 440,
            "id": 1984,
            "portPair": {
                "inputPort": {
                    "id": 1982,
                    "relativeHeight": 0.95
                },
                "name": "TesDHWPortHpDhw",
                "outputPort": {
                    "id": 1983,
                    "relativeHeight": 0.35454545454545455
                },
                "side": "left"
            },
            "trnsysId": 641
        },
        {
            "connectionId": 881,
            "id": 3926,
            "portPair": {
                "inputPort": {
                    "id": 3924,
                    "relativeHeight": 0.7
                },
                "name": "TesDHWPortDhwRecir",
                "outputPort": {
                    "id": 3925,
                    "relativeHeight": 0.9
                },
                "side": "right"
            },
            "trnsysId": 1271
        },
        {
            "connectionId": 886,
            "id": 3943,
            "portPair": {
                "inputPort": {
                    "id": 3941,
                    "relativeHeight": 0.05
                },
                "name": "TesDHWPortDHW",
                "outputPort": {
                    "id": 3942,
                    "relativeHeight": 0.95
                },
                "side": "right"
            },
            "trnsysId": 1277
        }
    ],
    "groupName": "defaultGroup",
    "heatExchangers": [
        {
            "connectionTrnsysId": 639,
            "id": 1976,
            "parentId": 1975,
            "portPair": {
                "inputPort": {
                    "id": 1977,
                    "relativeHeight": 0.3
                },
                "name": "SolarHx",
                "outputPort": {
                    "id": 1978,
                    "relativeHeight": 0.11818181818181818
                },
                "side": "left"
            },
            "width": 40
        }
    ],
    "height": 220.0,
    "id": 1975,
    "isHorizontallyFlipped": false,
    "isVerticallyFlipped": false,
    "position": [
        -681.9155092592591,
        -581.1302806712963
    ],
    "trnsysId": 638
}"""
        logger = _log.getLogger("root")
        (
            diagramViewMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, tmp_path)

        storageTank = self._deserializeStorageTank(storageTankLegacyJson, diagramViewMock)

        serializedStorageTank = storageTank.encode()[1]
        actualStorageTankJson = _json.dumps(
            serializedStorageTank, indent=4, sort_keys=True
        )

        assert actualStorageTankJson == expectedStorageTankJson

        self._deserializeStorageTank(actualStorageTankJson, diagramViewMock)

    @staticmethod
    def _deserializeStorageTank(storageTankLegacyJson, diagramViewMock):
        legacySerializedStorageTank = _json.loads(storageTankLegacyJson)

        storageTank = _st.StorageTank(trnsysType="StorageTank", parent=diagramViewMock)
        diagramViewMock.scene().addItem(storageTank)

        connections = []
        blocks = []
        storageTank.decode(legacySerializedStorageTank, connections, blocks)

        for heatExchanger in storageTank.heatExchangers:
            heatExchanger.initLoad()

        for connection in connections:
            connection.initLoad()

        return storageTank

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
