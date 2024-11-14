import pathlib as _pl

import pytest as _pt
from PyQt5.QtWidgets import QMessageBox

import trnsysGUI.storageTank.widget as stw
from tests.trnsysGUI import (
    utils,
)  # pylint complains when using .utils as utils.
from trnsysGUI.storageTank.ConfigureStorageDialog import ConfigureStorageDialog

_CURRENT_DIR = _pl.Path(__file__).parents[1]
_PROJECT_DIR = _CURRENT_DIR / "data/diagramForConfigStorageDialog"
_PROJECT_NAME = "diagramForConfigStorageDialog"


class TestConfigureStorageDialog:
    storageTank = None

    @_pt.fixture()
    def storageDialog(
        self, qtbot, monkeypatch
    ) -> ConfigureStorageDialog:
        monkeypatch.setattr(QMessageBox, "exec", lambda qbox: QMessageBox.Ok)

        mainWindow = utils.createMainWindow(_PROJECT_DIR, _PROJECT_NAME)
        qtbot.addWidget(mainWindow)
        self.storageTank = utils.getDesiredTrnsysObjectFromList(
            mainWindow.editor.trnsysObj, stw.StorageTank  # type: ignore
        )
        configureStorageDialog = self.storageTank.createStorageDialog()
        qtbot.addWidget(configureStorageDialog)
        return configureStorageDialog

    def testAddHxSuccess(self, storageDialog):
        hxInput = "90"
        hxOutput = "50"
        hxName = "Test hx"
        errors = []

        configureStorageDialog = storageDialog

        try:
            assert len(self.storageTank.heatExchangers) == 1
        except AssertionError as error:
            errors.append(error)

        configureStorageDialog.offsetLeI.setText(hxInput)
        configureStorageDialog.offsetLeO.setText(hxOutput)
        configureStorageDialog.hxNameLe.setText(hxName)
        configureStorageDialog.rButton.setChecked(True)
        configureStorageDialog.addHx()

        try:
            assert len(self.storageTank.heatExchangers) == 2
        except AssertionError as error:
            errors.append(error)

        try:
            assert self.storageTank.heatExchangers[1].displayName == hxName
        except AssertionError as error:
            errors.append(error)

        if errors:
            raise ExceptionGroup(f"Found {len(errors)} issues.", errors)

    def testAddHxMissingNameFailure(self, storageDialog):
        hxInput = "90"
        hxOutput = "50"

        configureStorageDialog = storageDialog
        configureStorageDialog.offsetLeI.setText(hxInput)
        configureStorageDialog.offsetLeO.setText(hxOutput)
        configureStorageDialog.rButton.setChecked(True)
        configureStorageDialog.addHx()

        assert (
            configureStorageDialog.msgb.text()
            == configureStorageDialog.MISSING_NAME_ERROR_MESSAGE
        )

    def testAddHxInvalidRangeFailure(self, storageDialog):
        hxInput = "90"
        hxOutput = "90"

        configureStorageDialog = storageDialog
        configureStorageDialog.offsetLeI.setText(hxInput)
        configureStorageDialog.offsetLeO.setText(hxOutput)
        configureStorageDialog.addHx()

        expectedErrorMessage = (
            f"At least {configureStorageDialog.minimumPortDistance}"
            f"% of difference needed and valid range (0, 100)"
        )

        assert configureStorageDialog.msgb.text() == expectedErrorMessage

    def testRemoveHxSuccess(self, storageDialog):
        configureStorageDialog = storageDialog
        assert len(self.storageTank.heatExchangers) == 1
        configureStorageDialog.leftHeatExchangersItemListWidget.item(
            0
        ).setSelected(True)
        configureStorageDialog.removeHxL()

        assert len(self.storageTank.heatExchangers) == 0

    def testAddPortPairSuccess(self, storageDialog):
        portPairInput = "1"
        portPairOutput = "99"

        configureStorageDialog = storageDialog
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.manlButton.setChecked(True)
        configureStorageDialog.addPortPair()

        assert len(self.storageTank.directPortPairs) == 2

    def testAddPortPairHeightFailure(self, storageDialog):
        portPairInput = "-1"
        portPairOutput = "100"

        configureStorageDialog = storageDialog
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.manlButton.setChecked(True)
        configureStorageDialog.addPortPair()

        assert (
            configureStorageDialog.msgb.text()
            == configureStorageDialog.PORT_HEIGHT_ERROR_MESSAGE
        )

    def testAddPortPairNoSideSelectedFailure(self, storageDialog):
        portPairInput = "9"
        portPairOutput = "42"

        configureStorageDialog = storageDialog
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.addPortPair()

        assert len(self.storageTank.directPortPairs) == 1
        assert (
            configureStorageDialog.msgb.text()
            == configureStorageDialog.NO_SIDE_SELECTED_ERROR_MESSAGE
        )

    def testRemovePortPairSuccess(self, storageDialog):
        configureStorageDialog = storageDialog
        assert len(self.storageTank.directPortPairs) == 1
        configureStorageDialog.rightDirectPortPairsItemListWidget.item(
            0
        ).setSelected(True)
        configureStorageDialog.removePortPairRight()

        assert len(self.storageTank.directPortPairs) == 0
