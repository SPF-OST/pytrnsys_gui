import itertools as _it
import json as _json
import logging as _log
import unittest.mock as _mock

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import pytrnsys.utils.serialization as _ser
import trnsysGUI.sideNrs as _snrs
from trnsysGUI.GenericBlock import GenericBlock  # type: ignore[attr-defined]
from trnsysGUI.GenericPortPairDlg import GenericPortPairDlg  # type: ignore[attr-defined]

_ALL_SIDES = [
    _snrs.SideNrs.LEFT,
    _snrs.SideNrs.TOP,
    _snrs.SideNrs.BOTTOM,
    _snrs.SideNrs.RIGHT,
]

_IMAGE_RESOURCE_PATH = "pkg_resource:images/GenericBlock.png"

# Generic blocks as saved before `GenericBlockModel`: the then current `BlockItemModel` plus
# `PortPairsNb` and `Imagesource`
_LEGACY_DICT_WITHOUT_VERSION = {
    ".__BlockDict__": True,
    "BlockName": "GenericBlock",
    "BlockDisplayName": "GenericBlock_1",
    "BlockPosition": [-287.0, -5.0],
    "ID": 1,
    "trnsysID": 1,
    "PortsIDIn": [2, 4],
    "PortsIDOut": [3, 5],
    "FlippedH": False,
    "FlippedV": False,
    "RotationN": 0,
    "PortPairsNb": [1, 0, 1, 0],
    "Imagesource": _IMAGE_RESOURCE_PATH,
}

_LEGACY_DICT_WITH_VERSION = {
    ".__BlockDict__": True,
    "__version__": "e8cfde2f-8239-4338-a5f0-63a7abb93900",
    "BlockName": "GenericBlock",
    "BlockDisplayName": "GenericBlock_1",
    "blockPosition": [-287.0, -5.0],
    "trnsysId": 1,
    "portsIdsIn": [2, 4],
    "portsIdsOut": [3, 5],
    "flippedH": False,
    "flippedV": False,
    "rotationN": 0,
    "PortPairsNb": [1, 0, 1, 0],
    "Imagesource": _IMAGE_RESOURCE_PATH,
}


class TestGenericBlock:
    @_pt.mark.parametrize("side", _ALL_SIDES)
    def testAddPortPairPutsPortsOnRequestedSide(self, side, qtbot) -> None:
        block = self._createGenericBlock(qtbot)

        block.addPortPair(side)

        assert block.portPairSides == [_snrs.SideNrs.RIGHT, side]
        assert block.inputs[1].side == side
        assert block.outputs[1].side == side

    def testEncodeDecodeRoundTrip(self, qtbot) -> None:
        block = self._createGenericBlock(qtbot)
        for side in [*_ALL_SIDES, _snrs.SideNrs.LEFT]:
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
        self._assertChildIdsMatchPortPairs(decodedBlock)

    @_pt.mark.parametrize(
        "legacyDict",
        [_LEGACY_DICT_WITHOUT_VERSION, _LEGACY_DICT_WITH_VERSION],
    )
    def testDecodeLegacyRaises(self, legacyDict, qtbot) -> None:
        block = self._createGenericBlock(qtbot)

        with _pt.raises(
            _ser.SerializationError,
            match="Generic block 'GenericBlock_1' was saved in a format that is no longer supported",
        ) as errorInfo:
            block.decode({**legacyDict}, [])

        assert isinstance(errorInfo.value.__cause__, _ser.SerializationError)

    def testRemovePortPairInDialog(self, qtbot) -> None:
        block = self._createGenericBlock(qtbot)
        dialog = GenericPortPairDlg(block)
        qtbot.addWidget(dialog)

        for radioButton in [dialog.rButtonTop, dialog.rButtonBottom]:
            radioButton.setChecked(True)
            dialog.addPortPair()

        dialog.listW.setCurrentRow(1)
        dialog.removePortPair()

        assert block.portPairSides == [
            _snrs.SideNrs.RIGHT,
            _snrs.SideNrs.BOTTOM,
        ]
        assert self._getListItemTexts(dialog) == [
            "Port pair at Right",
            "Port pair at Bottom",
        ]
        assert [p.side for p in [*block.inputs, *block.outputs]] == [
            _snrs.SideNrs.RIGHT,
            _snrs.SideNrs.BOTTOM,
            _snrs.SideNrs.RIGHT,
            _snrs.SideNrs.BOTTOM,
        ]
        self._assertChildIdsMatchPortPairs(block)

    def testCannotRemoveLastPortPairInDialog(self, qtbot) -> None:
        block = self._createGenericBlock(qtbot)
        dialog = GenericPortPairDlg(block)
        qtbot.addWidget(dialog)

        dialog.listW.setCurrentRow(0)

        assert not dialog.removeButton.isEnabled()

        dialog.removePortPair()

        assert block.portPairSides == [_snrs.SideNrs.RIGHT]
        assert self._getListItemTexts(dialog) == ["Port pair at Right"]

    @staticmethod
    def _getListItemTexts(dialog) -> list[str]:
        return [
            dialog.listW.item(i).text() for i in range(dialog.listW.count())
        ]

    @staticmethod
    def _assertChildIdsMatchPortPairs(block) -> None:
        assert len(block.childIds) == len(block.portPairSides)
        assert block.childIds[0] == block.trnsysId
        assert len(set(block.childIds)) == len(block.childIds)

    @staticmethod
    def _getPortIds(block: GenericBlock) -> list[tuple[int, int]]:
        return [(i.id, o.id) for i, o in zip(block.inputs, block.outputs)]

    @staticmethod
    def _getPortPositionsAndSides(block: GenericBlock) -> list[tuple]:
        return [
            (p.pos().x(), p.pos().y(), p.side)
            for p in [*block.inputs, *block.outputs]
        ]

    # Not annotated so that mypy doesn't complain about the attributes set on `editorMock`
    @staticmethod
    def _createGenericBlock(qtbot):
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
