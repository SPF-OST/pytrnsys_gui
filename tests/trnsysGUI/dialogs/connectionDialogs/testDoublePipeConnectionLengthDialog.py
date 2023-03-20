import unittest.mock as _m

import PyQt5.QtCore as _qtc

import trnsysGUI.dialogs.connectionDialogs.doublePipeConnectionLengthDialog as _dpcdlg
import trnsysGUI.errors as _errors


_SHOW_ERROR_FUNCTION_NAME = f"{_errors.__name__}.{_errors.showErrorMessageBox.__name__}"


class TestDoublePipeConnectionLengthDialog:  # pylint: disable = attribute-defined-outside-init
    def setup(self):
        self.connectionModel = _dpcdlg.ConnectionModel(5)
        self.dialog = _dpcdlg.DoublePipeConnectionLengthDialog(self.connectionModel)

    def _testHelper(self, bot, value, button="okButton"):
        bot.addWidget(self.dialog)
        self._clearAndWriteAndPressButton(bot, value, button)

    def _clearAndWriteAndPressButton(self, bot, value, button="okButton"):
        self.dialog.lineEdit.clear()
        bot.keyClicks(self.dialog.lineEdit, value)
        bot.mouseClick(getattr(self.dialog, button), _qtc.Qt.LeftButton)

    def testDialogLineEdit(self, qtbot):
        self._testHelper(qtbot, "7")
        assert self.connectionModel.lengthInM == 7

    def testDialogCancel(self, qtbot):
        self._testHelper(qtbot, "7", button="cancelButton")
        assert self.connectionModel.lengthInM == 5

    def testDialogRaises(self, qtbot):
        with _m.patch(_SHOW_ERROR_FUNCTION_NAME) as box:
            self._testHelper(qtbot, "-7")
            box.assert_called_with(errorMessage="Value must be positive.", title="Almost there")

    def testDialogInputAfterRaises(self, qtbot):
        with _m.patch(_SHOW_ERROR_FUNCTION_NAME):
            self._testHelper(qtbot, "-7")
            self._clearAndWriteAndPressButton(qtbot, "9")
            assert self.connectionModel.lengthInM == 9

    def teardown(self):
        self.dialog.close()
