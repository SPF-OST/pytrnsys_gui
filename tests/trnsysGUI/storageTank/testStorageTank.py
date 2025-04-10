import cgitb as _cgitb  # pylint: disable=deprecated-module
import json as _json
import logging as _log
import pathlib as _pl
import shutil as _sh
import time as _time
import typing as _tp
import unittest.mock as _mock

from PyQt5 import QtWidgets as _widgets

import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.hydraulicLoops.connectionsDefinitionMode as _cdm
import trnsysGUI.hydraulicLoops.model as _hlm
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.storageTank.widget as _st

# Sometimes PyQT crashes only returning with quite a cryptic error code. Sometimes, again, we can get
# a more helpful stack trace using the cgitb module.
_cgitb.enable(format="text")


class _StrictMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestStorageTank:
    DATA_DIR_PATH = _pl.Path(__file__).parent.parent / "data"
    ACTUAL_DIR_PATH = DATA_DIR_PATH / "actual"
    EXPECTED_DIR_PATH = DATA_DIR_PATH / "expected"
    LEGACY_JSON_PATH = DATA_DIR_PATH / "storageTankOldestFormat.json"

    def testDeserializeJsonFromLegacyFormatAndSerialize(
        self, tmp_path, qtbot  # pylint: disable=invalid-name  # /NOSONAR
    ):
        expectedPath = self.EXPECTED_DIR_PATH / "storageTankNewestFormat.json"
        expectedStorageTankJson = expectedPath.read_text()

        logger = _log.getLogger("root")
        (
            editorMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(
            logger, tmp_path, qtbot
        )

        legacyJson = self.LEGACY_JSON_PATH.read_text()
        storageTank = self._deserializeStorageTank(legacyJson, editorMock)

        serializedStorageTank = storageTank.encode()[1]
        actualStorageTankJson = _json.dumps(
            serializedStorageTank, indent=4, sort_keys=True
        )

        assert actualStorageTankJson == expectedStorageTankJson

        self._deserializeStorageTank(actualStorageTankJson, editorMock)

    @staticmethod
    def _deserializeStorageTank(storageTankLegacyJson, editorMock):
        legacySerializedStorageTank = _json.loads(storageTankLegacyJson)
        storageTank = _st.StorageTank(
            trnsysType="StorageTank",
            editor=editorMock,
            displayName=legacySerializedStorageTank["BlockDisplayName"],
        )  # pylint: disable=no-member

        blocks = []
        storageTank.decode(legacySerializedStorageTank, blocks)

        return storageTank

    def testExportDdck(self, qtbot):  # pylint: disable=invalid-name
        self._deleteAndRecreateEmptyActualDir()

        logger = _log.getLogger("root")
        (
            editorMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(
            logger, self.ACTUAL_DIR_PATH, qtbot
        )

        actualComponentDdckDirPath = self.ACTUAL_DIR_PATH / "ddck" / "TesDhw"
        actualComponentDdckDirPath.mkdir(parents=True, exist_ok=True)

        legacyJson = self.LEGACY_JSON_PATH.read_text()
        storageTank = self._deserializeStorageTank(legacyJson, editorMock)

        hydraulicLoops = _hlm.HydraulicLoops([])
        self._setupExternalConnectionMocks(storageTank, hydraulicLoops)

        storageTank.setHydraulicLoops(hydraulicLoops)

        storageTank.exportDck()

        actualDdckFilePath = actualComponentDdckDirPath / "TesDhw.ddck"
        actualDdckContent = actualDdckFilePath.read_text()
        print(actualDdckContent)

        expectedDdckContent = (
            self.EXPECTED_DIR_PATH / "TesDhw.ddck"
        ).read_text()

        assert actualDdckContent == expectedDdckContent

    def _deleteAndRecreateEmptyActualDir(self):
        if self.ACTUAL_DIR_PATH.exists():
            _sh.rmtree(self.ACTUAL_DIR_PATH)
        while self.ACTUAL_DIR_PATH.exists():
            _time.sleep(0.5)
        self.ACTUAL_DIR_PATH.mkdir()

    @classmethod
    def _setupExternalConnectionMocks(
        cls, storageTank: _st.StorageTank, hydraulicLoops: _hlm.HydraulicLoops
    ) -> None:
        for i, heatExchanger in enumerate(storageTank.heatExchangers):
            externalFromPortConnection = cls._createConnectionMock(
                f"hx{i}ExtFromPortConn", toPort=heatExchanger.port1
            )
            heatExchanger.port1.connectionList.append(
                externalFromPortConnection
            )

            externalToPortConnection = cls._createConnectionMock(
                f"hx{i}ExtToPortConn", fromPort=heatExchanger.port2
            )
            heatExchanger.port2.connectionList.append(externalToPortConnection)

            cls._addLoop(
                externalFromPortConnection,
                externalToPortConnection,
                i,
                hydraulicLoops,
                namePrefix="hx",
            )

        for i, directPortPair in enumerate(storageTank.directPortPairs):
            externalFromPortConnection = cls._createConnectionMock(
                f"dpp{i}ExtFromPortConn", toPort=directPortPair.fromPort
            )
            directPortPair.fromPort.connectionList.append(
                externalFromPortConnection
            )

            externalToPortConnection = cls._createConnectionMock(
                f"dpp{i}ExtToPortConn", fromPort=directPortPair.toPort
            )
            directPortPair.toPort.connectionList.append(
                externalToPortConnection
            )

            cls._addLoop(
                externalFromPortConnection,
                externalToPortConnection,
                i,
                hydraulicLoops,
                namePrefix="dp",
            )

    @classmethod
    def _addLoop(  # pylint: disable=too-many-positional-arguments, too-many-arguments
        cls,
        externalFromPortConnection,
        externalToPortConnection,
        i,
        hydraulicLoops,
        namePrefix,
    ):
        fluid = _hlm.Fluids.BRINE if i % 2 == 0 else _hlm.Fluids.WATER
        connections = [externalFromPortConnection, externalToPortConnection]
        name = _hlm.UserDefinedName(f"{namePrefix}Loop{i}")

        connectionsDefinitionMode = (
            _cdm.ConnectionsDefinitionMode.LOOP_WIDE_DEFAULTS
        )
        loop = _hlm.HydraulicLoop(
            name, fluid, connectionsDefinitionMode, connections=connections
        )
        hydraulicLoops.addLoop(loop)

    @staticmethod
    def _createConnectionMock(
        displayName: str, fromPort=_StrictMock(), toPort=_StrictMock()
    ) -> _spc.SinglePipeConnection:
        modelPipe = _mfn.Pipe(
            _mfn.PortItem("In", _mfn.PortItemDirection.INPUT),
            _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT),
        )

        def getInternalPiping() -> _ip.InternalPiping:
            return _ip.InternalPiping(
                [modelPipe],
                {modelPipe.fromPort: fromPort, modelPipe.toPort: toPort},
            )

        def getModelPipe(portItemType: _mfn.PortItemType) -> _mfn.Pipe:
            assert portItemType == _mfn.PortItemType.STANDARD

            return modelPipe

        mock = _StrictMock(
            displayName=displayName,
            getDisplayName=lambda: displayName,
            fromPort=fromPort,
            toPort=toPort,
            modelPipe=modelPipe,
            getModelPipe=getModelPipe,
            getInternalPiping=getInternalPiping,
            hasDdckPlaceHolders=lambda: False,
            shallRenameOutputTemperaturesInHydraulicFile=lambda: False,
        )

        return _tp.cast(_spc.SinglePipeConnection, mock)

    @staticmethod
    def _createDiagramViewMocksAndOtherObjectsToKeepAlive(
        logger, projectFolder, bot
    ):
        mainWindow = _widgets.QMainWindow()

        bot.addWidget(mainWindow)

        editorMock = _widgets.QWidget(parent=mainWindow)
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
                "getConnID",
            ],
        )
        editorMock.moveDirectPorts = True
        editorMock.snapGrid = False
        editorMock.alignMode = False

        editorMock.idGen.getID = lambda: 7701
        editorMock.idGen.getTrnsysID = lambda: 7702
        editorMock.idGen.getStoragenTes = lambda: 7703
        editorMock.idGen.getStorageType = lambda: 7704
        editorMock.idGen.getConnID = lambda: 7705

        graphicsScene = _widgets.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = graphicsScene

        mainWindow.setCentralWidget(editorMock)
        mainWindow.showMinimized()

        return editorMock, [mainWindow, graphicsScene]
