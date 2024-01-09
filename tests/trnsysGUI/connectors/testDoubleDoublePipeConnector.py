import cgitb as _cgitb  # pylint: disable=deprecated-module
import logging as _log
import typing as _tp
import unittest.mock as _mock

from PyQt5 import QtWidgets as _widgets

import trnsysGUI.connection.connectors.doubleDoublePipeConnector as _ddpc
import trnsysGUI.connection.doublePipeConnection as _dpc
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn

# Sometimes PyQT crashes only returning with quite a cryptic error code. Sometimes, again, we can get
# a more helpful stack trace using the cgitb module.
_cgitb.enable(format="text")


class _StrictMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


_EXPECTED_TEXT = """\
! BEGIN DPCnr
! cold pipe
UNIT 1 TYPE 2221
PARAMETERS 2
mfrSolverAbsTol
dpTIniCold
INPUTS 3
MDPCnrCold_A ToutputConnectionCold TinputConnectionCold
***
0 dpTIniCold dpTIniCold
EQUATIONS 1
TDPCnrCold = [1,1]

! hot pipe
UNIT 2 TYPE 2221
PARAMETERS 2
mfrSolverAbsTol
dpTIniHot
INPUTS 3
MDPCnrHot_A TinputConnectionHot ToutputConnectionHot
***
0 dpTIniHot dpTIniHot
EQUATIONS 1
TDPCnrHot = [2,1]
! END DPCnr


"""


class TestDoubleDoublePipeConnector:
    def test(self, tmp_path, qtbot):  # pylint: disable=invalid-name  # /NOSONAR
        connector = self._createConnector(tmp_path, qtbot)

        unitNumber = 1
        text, nextUnitNumber = connector.exportPipeAndTeeTypesForTemp(unitNumber)

        assert nextUnitNumber == unitNumber + 2
        assert text == _EXPECTED_TEXT

    @classmethod
    def _createConnector(cls, tmp_path, bot):  # pylint: disable=invalid-name  # /NOSONAR
        logger = _log.getLogger("root")

        (
            editorMock,
            objectsNeededToBeKeptAliveWhileTanksAlive,  # pylint: disable=unused-variable
        ) = cls._createEditorMockAndOtherObjectsToKeepAlive(logger, tmp_path, bot)

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
    def _createEditorMockAndOtherObjectsToKeepAlive(logger, projectPath, bot):
        # todo: provide this class as a TestHelper class. see TestStorageTank  # pylint: disable=fixme
        mainWindow = _widgets.QMainWindow()

        bot.addWidget(mainWindow)

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

        return editorMock, [mainWindow, graphicsScene]
