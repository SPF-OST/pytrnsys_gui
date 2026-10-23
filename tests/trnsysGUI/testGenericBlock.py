import itertools as _it
import json as _json
import logging as _log
import unittest.mock as _mock

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import trnsysGUI.sideNrs as _snrs
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]

_SIDES = [
    _snrs.SideNrs.LEFT,
    _snrs.SideNrs.TOP,
    _snrs.SideNrs.BOTTOM,
    _snrs.SideNrs.LEFT,
]


class TestGenericBlock:
    @_pt.mark.parametrize("side", _SIDES[:3] + [_snrs.SideNrs.RIGHT])
    def testAddPortPairPutsPortsOnRequestedSide(self, side, qtbot) -> None:
        block = self._createGenericBlock(qtbot)

        block.addPortPair(side)

        assert block.portPairSides == [_snrs.SideNrs.RIGHT, side]
        assert block.inputs[1].side == side
        assert block.outputs[1].side == side

    def testEncodeDecodeRoundTrip(self, qtbot) -> None:
        block = self._createGenericBlock(qtbot)
        for side in _SIDES:
            block.addPortPair(side)
        block.setPos(-20, -360)

        _, encodedDict = block.encode()
        # As written to and read from the project file
        encodedDict = _json.loads(_json.dumps(encodedDict))

        decodedBlock = self._createGenericBlock(qtbot)
        resBlockList: list = []
        decodedBlock.decode(encodedDict, resBlockList)

        assert resBlockList == [decodedBlock]
        assert decodedBlock.displayName == block.displayName
        assert decodedBlock.pos() == block.pos()
        assert decodedBlock.portPairSides == block.portPairSides
        assert self._getPortIds(decodedBlock) == self._getPortIds(block)
        assert self._getPortPositionsAndSides(
            decodedBlock
        ) == self._getPortPositionsAndSides(block)

    def testDecodeWithoutPortPairSides(self, qtbot) -> None:
        block = self._createGenericBlock(qtbot)
        block.addPortPair(_snrs.SideNrs.TOP)

        _, encodedDict = block.encode()
        del encodedDict["PortPairSides"]

        decodedBlock = self._createGenericBlock(qtbot)
        decodedBlock.decode(encodedDict, [])

        assert decodedBlock.portPairSides == [
            _snrs.SideNrs.RIGHT,
            _snrs.SideNrs.TOP,
        ]

    @staticmethod
    def _getPortIds(block: GenericBlock) -> list[tuple[int, int]]:
        return [(i.id, o.id) for i, o in zip(block.inputs, block.outputs)]

    @staticmethod
    def _getPortPositionsAndSides(block: GenericBlock) -> list[tuple]:
        return [
            (p.pos().x(), p.pos().y(), p.side)
            for p in [*block.inputs, *block.outputs]
        ]

    @staticmethod
    def _createGenericBlock(qtbot) -> GenericBlock:
        mainWindow = _qtw.QMainWindow()
        qtbot.addWidget(mainWindow)

        editorMock = _qtw.QWidget(parent=mainWindow)
        editorMock.logger = _log.getLogger("root")
        editorMock.connectionList = []
        editorMock.trnsysObj = []
        editorMock.splitter = _mock.Mock(name="splitter")
        editorMock.moveDirectPorts = True
        editorMock.snapGrid = False
        editorMock.alignMode = False

        ids = _it.count(7701)
        editorMock.idGen = _mock.Mock(
            name="idGen", spec_set=["getID", "getTrnsysID"]
        )
        editorMock.idGen.getID = lambda: next(ids)
        editorMock.idGen.getTrnsysID = lambda: next(ids)

        editorMock.diagramScene = _qtw.QGraphicsScene(parent=editorMock)
        mainWindow.setCentralWidget(editorMock)

        return GenericBlock("GenericBlock", editorMock, "Bolr")
