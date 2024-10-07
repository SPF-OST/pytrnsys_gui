import trnsysGUI.storageTank.widget as stw
from tests.trnsysGUI.utils.Utils import Utils

import pathlib as _pl
import PyQt5.QtCore as _core

_CURRENT_DIR = _pl.Path(__file__).parent
_PROJECT_DIR = _CURRENT_DIR / ".." / "data" / "diagramForConfigStorageDialog"
_PROJECT_NAME = "diagramForConfigStorageDialog"

class TestConfigureStorageDialog:

    storageTank=None

    def triggerStorgeDialog(self, qtbot):
        mainWindow = Utils.createMainWindow(_PROJECT_DIR, _PROJECT_NAME)
        qtbot.addWidget(mainWindow)
        self.storageTank = Utils.getDesiredTrnsysObjectFromList(mainWindow.editor.trnsysObj, stw.StorageTank)
        configureStorageDialog = self.storageTank.mouseDoubleClickEvent(_core.QEvent.MouseButtonDblClick, isTest=True)
        configureStorageDialog.isTest = True
        qtbot.addWidget(configureStorageDialog)
        return configureStorageDialog

    def testAddHxSuccess(self,qtbot):
        HX_INPUT = "90"
        HX_OUTPUT = "50"
        HX_NAME = "Test hx"
        errors = []

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        try:
            assert len(self.storageTank.heatExchangers) == 1
        except AssertionError as error:
            errors.append(error)
        configureStorageDialog.offsetLeI.setText(HX_INPUT)
        configureStorageDialog.offsetLeO.setText(HX_OUTPUT)
        configureStorageDialog.hxNameLe.setText(HX_NAME)
        configureStorageDialog.rButton.setChecked(True)
        configureStorageDialog.addHx()
        print(self.storageTank.heatExchangers)
        try:
            assert len(self.storageTank.heatExchangers) == 2
        except AssertionError as error:
            errors.append(error)
        try:
            assert self.storageTank.heatExchangers[1].displayName == HX_NAME
        except AssertionError as error:
            errors.append(error)
        if errors:
            raise ExceptionGroup(f"Found {len(errors)} issues.", errors)

    def testAddHxMissingNameFailure(self, qtbot):
        HX_INPUT = "90"
        HX_OUTPUT = "50"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        configureStorageDialog.offsetLeI.setText(HX_INPUT)
        configureStorageDialog.offsetLeO.setText(HX_OUTPUT)
        configureStorageDialog.rButton.setChecked(True)
        configureStorageDialog.addHx()

        assert (configureStorageDialog.msgb.text() == configureStorageDialog.MISSING_NAME_ERROR_MESSAGE)

    def testAddHxInvalidRangeFailure(self, qtbot):
        HX_INPUT = "90"
        HX_OUTPUT = "90"


        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        EXPECTED_ERROR_MESSAGE = (f"At least {configureStorageDialog.minimumPortDistance}% of difference needed and valid range (0, 100)")
        configureStorageDialog.offsetLeI.setText(HX_INPUT)
        configureStorageDialog.offsetLeO.setText(HX_OUTPUT)
        configureStorageDialog.addHx()

        assert (configureStorageDialog.msgb.text() == EXPECTED_ERROR_MESSAGE)
        # def assert_async():
        #     try:
        #         assert (configureStorageDialog.msgb.text() == EXPECTED_ERROR_MESSAGE)
        #     except AttributeError as error:
        #         print(error)
        #
        #
        # def handle_dialog():
        #     messagebox = _qtWidgets.QApplication.activeWindow()
        #     ok_button = messagebox.button(_qtWidgets.QMessageBox.Ok)
        #     qtbot.mouseClick(ok_button, _core.Qt.LeftButton, delay=1)


        # Could not get qtTimer and waitUntil to work as excpected
        # qtbot.waitUntil(assert_async)
        # configureStorageDialog.addHx()
         # _core.QTimer.singleShot(100, handle_dialog())


        # Interacting with ui through qtbot also does not work after exec_ method is called
        # qtbot.mouseClick(configureStorageDialog.addButton, _core.Qt.LeftButton, delay=1)
        # ok_button = configureStorageDialog.msgb.button(_qtWidgets.QMessageBox.Ok)
        # qtbot.mouseClick(ok_button, _core.Qt.LeftButton, delay=1)

    def testRemoveHxSuccess(self, qtbot):
        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        assert len(self.storageTank.heatExchangers) == 1
        configureStorageDialog.leftHeatExchangersItemListWidget.item(0).setSelected(True)
        configureStorageDialog.removeHxL()

        assert len(self.storageTank.heatExchangers) == 0

    def testAddPortPairSuccess(self, qtbot):
        PORT_PAIR_INPUT="1"
        PORT_PAIR_OUTPUT="99"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        configureStorageDialog.manPortLeI.setText(PORT_PAIR_INPUT)
        configureStorageDialog.manPortLeO.setText(PORT_PAIR_OUTPUT)
        configureStorageDialog.manlButton.setChecked(True)
        configureStorageDialog.addPortPair()

        assert len(self.storageTank.directPortPairs)==2

    def testAddPortPairHeightFailure(self, qtbot):
        PORT_PAIR_INPUT="-1"
        PORT_PAIR_OUTPUT="100"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        configureStorageDialog.manPortLeI.setText(PORT_PAIR_INPUT)
        configureStorageDialog.manPortLeO.setText(PORT_PAIR_OUTPUT)
        configureStorageDialog.manlButton.setChecked(True)
        configureStorageDialog.addPortPair()

        assert (configureStorageDialog.msgb.text() == configureStorageDialog.PORT_HEIGHT_ERROR_MESSAGE)

    def testAddPortPairNoSideSelectedFailure(self, qtbot):
        PORT_PAIR_INPUT = "-1"
        PORT_PAIR_OUTPUT = "100"

        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        configureStorageDialog.manPortLeI.setText(PORT_PAIR_INPUT)
        configureStorageDialog.manPortLeO.setText(PORT_PAIR_OUTPUT)
        configureStorageDialog.addPortPair()

        assert len(self.storageTank.directPortPairs) == 1

    def testRemovePortPairSuccess(self, qtbot):
        configureStorageDialog = self.triggerStorgeDialog(qtbot)
        assert len(self.storageTank.directPortPairs) == 1
        configureStorageDialog._rightDirectPortPairsItemListWidget.item(0).setSelected(True)
        configureStorageDialog.removePortPairRight()

        assert len(self.storageTank.directPortPairs) == 0