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


class _StrictMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestDoubleDoublePipeConnector:
    def test(self, tmp_path):  # pylint: disable=invalid-name
        connector = self._createConnector(tmp_path)

        unitNumber = 1
        text, nextUnitNumber = connector.exportPipeAndTeeTypesForTemp(unitNumber)

        assert nextUnitNumber == unitNumber + 2
        assert text == """\
UNIT 1 TYPE 222
INPUTS 3
MDPCnrHot_A TinputConnectionHot ToutputConnectionHot
***
0 20 20

EQUATIONS 1
TDPCnrHot = [1,1]


UNIT 2 TYPE 222
INPUTS 3
MDPCnrCold_A ToutputConnectionCold TinputConnectionCold
***
0 20 20

EQUATIONS 1
TDPCnrCold = [2,1]

"""

    @classmethod
    def _createConnector(cls, tmp_path):  # pylint: disable=invalid-name:
        logger = _log.getLogger("root")

        (
            editorMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = cls._createEditorMockAndOtherObjectsToKeepAlive(logger, tmp_path)

        connector = _ddpc.DoubleDoublePipeConnector(
            editor=editorMock,
            trnsysType="DPCnr",
            displayName="DPCnr",
        )

        externalFromPortConnection = cls._createConnectionMock("inputConnection", toPort=connector.inputs[0])
        connector.inputs[0].connectionList.append(externalFromPortConnection)

        externalToPortConnection = cls._createConnectionMock("outputConnection", fromPort=connector.outputs[0])
        connector.outputs[0].connectionList.append(externalToPortConnection)

        return connector

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
            modelPortItemsToGraphicalPortItem = (
                coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
            )
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
    def _createEditorMockAndOtherObjectsToKeepAlive(logger, projectPath):
        # todo: provide this class as a TestHelper class. see TestStorageTank  # pylint: disable=fixme
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
            ],
        )
        editorMock.moveDirectPorts = True
        editorMock.editorMode = 1
        editorMock.snapGrid = False
        editorMock.alignMode = False

        editorMock.idGen.getID = lambda: 7701
        editorMock.idGen.getTrnsysID = lambda: 7702

        graphicsScene = _widgets.QGraphicsScene(parent=editorMock)
        editorMock.diagramScene = graphicsScene

        mainWindow.setCentralWidget(editorMock)
        mainWindow.showMinimized()

        return editorMock, [application, mainWindow, graphicsScene]
