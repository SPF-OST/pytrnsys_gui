import cgitb as _cgitb
import logging as _log
import unittest.mock as _mock
import typing as _tp

from PyQt5 import QtWidgets as _widgets

import trnsysGUI.connectors.doubleDoublePipeConnector as _ddpc
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.internalPiping as _ip
import trnsysGUI.connection.doublePipeConnection as _dpc

# Sometimes PyQT crashes only returning with quite a cryptic error code. Sometimes, again, we can get
# a more helpful stack trace using the cgitb module.
_cgitb.enable(format="text")


def getUnitText(version1, version2):
    unit_text = 'UNIT 5 TYPE 222\n' \
           'INPUTS 3\n' \
           'MDPCnr7701Hot_A Thx1ExtFromPortConnHot Tdpp1ExtToPortConnHot\n' \
           '***\n' \
           '0 20 20\n' \
           '\n' \
           'EQUATIONS 1\n' \
           f'TDPCnr7701{version1} = [5,1]\n' \
           '\n' \
           '\n' \
           'UNIT 6 TYPE 222\n' \
           'INPUTS 3\n' \
           'MDPCnr7701Cold_A Tdpp1ExtToPortConnCold Thx1ExtFromPortConnCold\n' \
           '***\n0 20 20\n' \
           '\n' \
           'EQUATIONS 1\n' \
           f'TDPCnr7701{version2} = [6,1]\n' \
           '\n' \
           '\n'
    return unit_text


class _StrictMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestDoubleDoublePipeConnector:
    def test_connection_writes_both_HOT_and_COLD_entries(self, tmp_path):
        logger = _log.getLogger("root")
        (
            diagramViewMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, tmp_path)

        ddpConnector = _ddpc.DoubleDoublePipeConnector(
            trnsysType="DPCnr",
            parent=diagramViewMock,
            displayNamePrefix="DPCnr",
        )  # pylint: disable=no-member
        diagramViewMock.scene().addItem(ddpConnector)

        externalFromPortConnection = self._createConnectionMock(f"hx1ExtFromPortConn", toPort=ddpConnector.inputs[0])
        ddpConnector.inputs[0].connectionList.append(externalFromPortConnection)
        externalToPortConnection = self._createConnectionMock(f"dpp1ExtToPortConn", fromPort=ddpConnector.outputs[0])
        ddpConnector.outputs[0].connectionList.append(externalToPortConnection)
        text, newTemp = ddpConnector.exportPipeAndTeeTypesForTemp(5)
        assert newTemp == 7
        assert text == getUnitText('Hot', 'Cold')

    def test_connection_does_not_write_both_HOT_entries(self, tmp_path):
        logger = _log.getLogger("root")
        (
            diagramViewMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, tmp_path)

        ddpConnector = _ddpc.DoubleDoublePipeConnector(
            trnsysType="DPCnr",
            parent=diagramViewMock,
            displayNamePrefix="DPCnr",
        )  # pylint: disable=no-member
        diagramViewMock.scene().addItem(ddpConnector)

        externalFromPortConnection = self._createConnectionMock(f"hx1ExtFromPortConn", toPort=ddpConnector.inputs[0])
        ddpConnector.inputs[0].connectionList.append(externalFromPortConnection)
        externalToPortConnection = self._createConnectionMock(f"dpp1ExtToPortConn", fromPort=ddpConnector.outputs[0])
        ddpConnector.outputs[0].connectionList.append(externalToPortConnection)
        text, newTemp = ddpConnector.exportPipeAndTeeTypesForTemp(5)
        assert newTemp == 7
        assert text != getUnitText('Hot', 'Hot')

    def test_connection_does_not_write_both_COLD_entries(self, tmp_path):
        logger = _log.getLogger("root")
        (
            diagramViewMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = self._createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, tmp_path)

        ddpConnector = _ddpc.DoubleDoublePipeConnector(
            trnsysType="DPCnr",
            parent=diagramViewMock,
            displayNamePrefix="DPCnr",
        )  # pylint: disable=no-member
        diagramViewMock.scene().addItem(ddpConnector)

        externalFromPortConnection = self._createConnectionMock(f"hx1ExtFromPortConn", toPort=ddpConnector.inputs[0])
        ddpConnector.inputs[0].connectionList.append(externalFromPortConnection)
        externalToPortConnection = self._createConnectionMock(f"dpp1ExtToPortConn", fromPort=ddpConnector.outputs[0])
        ddpConnector.outputs[0].connectionList.append(externalToPortConnection)
        text, newTemp = ddpConnector.exportPipeAndTeeTypesForTemp(5)
        assert newTemp == 7
        assert text != getUnitText('Cold', 'Cold')

    @staticmethod
    def _createConnectionMock(
        displayName: str, fromPort=_StrictMock(), toPort=_StrictMock()
    ) -> _dpc.DoublePipeConnection:
        coldInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
        coldOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
        coldModelPipe = _mfn.Pipe(coldInput, coldOutput, "Cold")

        hotInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
        hotOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
        hotModelPipe = _mfn.Pipe(hotInput, hotOutput, "Hot")

        def getInternalPiping() -> _ip.InternalPiping:
            coldModelPortItemsToGraphicalPortItem = {coldModelPipe.fromPort: toPort, coldModelPipe.toPort: fromPort}
            hotModelPortItemsToGraphicalPortItem = {hotModelPipe.fromPort: fromPort, hotModelPipe.toPort: toPort}
            modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
            return _ip.InternalPiping([coldModelPipe, hotModelPipe], modelPortItemsToGraphicalPortItem)

        mock = _StrictMock(
            displayName=displayName,
            getDisplayName=lambda: displayName,
            fromPort=fromPort,
            toPort=toPort,
            _hotPipe=hotModelPipe,
            _coldPipe=coldModelPipe,
            getInternalPiping=getInternalPiping,
            hasDdckPlaceHolders=lambda: False,
            shallRenameOutputTemperaturesInHydraulicFile=lambda: False,
        )

        return _tp.cast(_dpc.DoublePipeConnection, mock)

    @staticmethod
    def _createDiagramViewMocksAndOtherObjectsToKeepAlive(logger, projectPath):
        application = _widgets.QApplication([])

        mainWindow = _widgets.QMainWindow()

        editorMock = _widgets.QWidget(parent=mainWindow)
        editorMock.connectionList = []
        editorMock.logger = logger
        editorMock.trnsysObj = []
        editorMock.projectPath = str(projectPath)
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

        editorMock.idGen.getID = lambda: 7701
        editorMock.idGen.getTrnsysID = lambda: 7702
        editorMock.idGen.getStoragenTes = lambda: 7703
        editorMock.idGen.getStorageType = lambda: 7704
        editorMock.idGen.getConnID = lambda: 7705

        graphicsScene = _widgets.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = graphicsScene

        diagramViewMock = _widgets.QGraphicsView(graphicsScene, parent=editorMock)
        diagramViewMock.logger = logger

        mainWindow.setCentralWidget(editorMock)
        mainWindow.showMinimized()

        return diagramViewMock, [application, mainWindow, editorMock, graphicsScene]
