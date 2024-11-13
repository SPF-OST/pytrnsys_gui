import pathlib as _pl

import pytest
from PyQt5.QtWidgets import QMessageBox

import trnsysGUI.storageTank.widget as stw
from tests.trnsysGUI import (
    utils,
)  # pylint complains when using .utils as utils.
from trnsysGUI.storageTank.ConfigureStorageDialog import ConfigureStorageDialog

_CURRENT_DIR = _pl.Path(__file__).parent
_PROJECT_DIR = _CURRENT_DIR / ".." / "data" / "diagramForConfigStorageDialog"
_PROJECT_NAME = "diagramForConfigStorageDialog"


class TestConfigureStorageDialog:
    storageTank = None

    @pytest.fixture()
    def triggerStorageDialog(
        self, qtbot, monkeypatch
    ) -> ConfigureStorageDialog:
        monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Ok)

        mainWindow = utils.createMainWindow(_PROJECT_DIR, _PROJECT_NAME)
        qtbot.addWidget(mainWindow)
        self.storageTank = utils.getDesiredTrnsysObjectFromList(
            mainWindow.editor.trnsysObj, stw.StorageTank  # type: ignore
        )
        configureStorageDialog = self.storageTank.createStorageDialog()
        qtbot.addWidget(configureStorageDialog)
        return configureStorageDialog

    def testAddHxSuccess(self, triggerStorageDialog):
        hxInput = "90"
        hxOutput = "50"
        hxName = "Test hx"
        errors = []

        configureStorageDialog = triggerStorageDialog

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

    def testAddHxMissingNameFailure(self, triggerStorageDialog):
        hxInput = "90"
        hxOutput = "50"

        configureStorageDialog = triggerStorageDialog
        configureStorageDialog.offsetLeI.setText(hxInput)
        configureStorageDialog.offsetLeO.setText(hxOutput)
        configureStorageDialog.rButton.setChecked(True)
        configureStorageDialog.addHx()

        assert (
            configureStorageDialog.msgb.text()
            == configureStorageDialog.MISSING_NAME_ERROR_MESSAGE
        )

    def testAddHxInvalidRangeFailure(self, triggerStorageDialog):
        hxInput = "90"
        hxOutput = "90"

        configureStorageDialog = triggerStorageDialog
        configureStorageDialog.offsetLeI.setText(hxInput)
        configureStorageDialog.offsetLeO.setText(hxOutput)
        configureStorageDialog.addHx()

        expectedErrorMessage = (
            f"At least {configureStorageDialog.minimumPortDistance}"
            f"% of difference needed and valid range (0, 100)"
        )

        assert configureStorageDialog.msgb.text() == expectedErrorMessage

    def testRemoveHxSuccess(self, triggerStorageDialog):
        configureStorageDialog = triggerStorageDialog
        assert len(self.storageTank.heatExchangers) == 1
        configureStorageDialog.leftHeatExchangersItemListWidget.item(
            0
        ).setSelected(True)
        configureStorageDialog.removeHxL()

        assert len(self.storageTank.heatExchangers) == 0

    def testAddPortPairSuccess(self, triggerStorageDialog):
        portPairInput = "1"
        portPairOutput = "99"

        configureStorageDialog = triggerStorageDialog
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.manlButton.setChecked(True)
        configureStorageDialog.addPortPair()

        assert len(self.storageTank.directPortPairs) == 2

    def testAddPortPairHeightFailure(self, triggerStorageDialog):
        portPairInput = "-1"
        portPairOutput = "100"

        configureStorageDialog = triggerStorageDialog
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.manlButton.setChecked(True)
        configureStorageDialog.addPortPair()

        assert (
            configureStorageDialog.msgb.text()
            == configureStorageDialog.PORT_HEIGHT_ERROR_MESSAGE
        )

    def testAddPortPairNoSideSelectedFailure(self, triggerStorageDialog):
        portPairInput = "9"
        portPairOutput = "42"

        configureStorageDialog = triggerStorageDialog
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.addPortPair()

        assert len(self.storageTank.directPortPairs) == 1
        assert (
            configureStorageDialog.msgb.text()
            == configureStorageDialog.NO_SIDE_SELECTED_ERROR_MESSAGE
        )

    def testRemovePortPairSuccess(self, triggerStorageDialog):
        configureStorageDialog = triggerStorageDialog
        assert len(self.storageTank.directPortPairs) == 1
        configureStorageDialog.rightDirectPortPairsItemListWidget.item(
            0
        ).setSelected(True)
        configureStorageDialog.removePortPairRight()

        assert len(self.storageTank.directPortPairs) == 0
