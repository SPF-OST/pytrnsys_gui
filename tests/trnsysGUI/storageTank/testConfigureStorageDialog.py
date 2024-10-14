import pathlib as _pl
import PyQt5.QtCore as _core

import trnsysGUI.storageTank.widget as stw
from tests.trnsysGUI import utils  # pylint complains when using .utils as utils.

_CURRENT_DIR = _pl.Path(__file__).parent
_PROJECT_DIR = _CURRENT_DIR / ".." / "data" / "diagramForConfigStorageDialog"
_PROJECT_NAME = "diagramForConfigStorageDialog"


class TestConfigureStorageDialog:

    storageTank = None

    def triggerStorgeDialog(self, qtbot):
        mainWindow = utils.createMainWindow(_PROJECT_DIR, _PROJECT_NAME)
        qtbot.addWidget(mainWindow)
        self.storageTank = utils.getDesiredTrnsysObjectFromList(mainWindow.editor.trnsysObj, stw.StorageTank)
        configureStorageDialog = self.storageTank.mouseDoubleClickEvent(_core.QEvent.MouseButtonDblClick, isTest=True)
        configureStorageDialog.isTest = True
        qtbot.addWidget(configureStorageDialog)
        return configureStorageDialog

    def testAddHxSuccess(self, qtbot):
        hxInput = "90"
        hxOutput = "50"
        hxName = "Test hx"
        errors = []

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        try:
            assert len(self.storageTank.heatExchangers) == 1
        except AssertionError as error:
            errors.append(error)
        configureStorageDialog.offsetLeI.setText(hxInput)
        configureStorageDialog.offsetLeO.setText(hxOutput)
        configureStorageDialog.hxNameLe.setText(hxName)
        configureStorageDialog.rButton.setChecked(True)
        configureStorageDialog.addHx()
        print(self.storageTank.heatExchangers)
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

    def testAddHxMissingNameFailure(self, qtbot):
        hxInput = "90"
        hxOutput = "50"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        configureStorageDialog.offsetLeI.setText(hxInput)
        configureStorageDialog.offsetLeO.setText(hxOutput)
        configureStorageDialog.rButton.setChecked(True)
        configureStorageDialog.addHx()

        assert configureStorageDialog.msgb.text() == configureStorageDialog.MISSING_NAME_ERROR_MESSAGE

    def testAddHxInvalidRangeFailure(self, qtbot):
        hxInput = "90"
        hxOutput = "90"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        expectedErrorMessage = (
            f"At least {configureStorageDialog.minimumPortDistance}" f"% of difference needed and valid range (0, 100)"
        )
        configureStorageDialog.offsetLeI.setText(hxInput)
        configureStorageDialog.offsetLeO.setText(hxOutput)
        configureStorageDialog.addHx()

        assert configureStorageDialog.msgb.text() == expectedErrorMessage

    def testRemoveHxSuccess(self, qtbot):
        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        assert len(self.storageTank.heatExchangers) == 1
        configureStorageDialog.leftHeatExchangersItemListWidget.item(0).setSelected(True)
        configureStorageDialog.removeHxL()

        assert len(self.storageTank.heatExchangers) == 0

    def testAddPortPairSuccess(self, qtbot):
        portPairInput = "1"
        portPairOutput = "99"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.manlButton.setChecked(True)
        configureStorageDialog.addPortPair()

        assert len(self.storageTank.directPortPairs) == 2

    def testAddPortPairHeightFailure(self, qtbot):
        portPairInput = "-1"
        portPairOutput = "100"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.manlButton.setChecked(True)
        configureStorageDialog.addPortPair()

        assert configureStorageDialog.msgb.text() == configureStorageDialog.PORT_HEIGHT_ERROR_MESSAGE

    def testAddPortPairNoSideSelectedFailure(self, qtbot):
        portPairInput = "-1"
        portPairOutput = "100"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        configureStorageDialog.manPortLeI.setText(portPairInput)
        configureStorageDialog.manPortLeO.setText(portPairOutput)
        configureStorageDialog.addPortPair()

        assert len(self.storageTank.directPortPairs) == 1

    def testRemovePortPairSuccess(self, qtbot):
        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        assert len(self.storageTank.directPortPairs) == 1
        configureStorageDialog.rightDirectPortPairsItemListWidget.item(0).setSelected(True)
        configureStorageDialog.removePortPairRight()

        assert len(self.storageTank.directPortPairs) == 0
