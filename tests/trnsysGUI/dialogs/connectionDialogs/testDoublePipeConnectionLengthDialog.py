import unittest.mock as _m
import pytest as _pt

from PyQt5 import QtCore

import trnsysGUI.dialogs.connectionDialogs.doublePipeConnectionLengthDialog as _dpcdlg


class TestDoublePipeConnectionLengthDialog:  # pylint: disable = attribute-defined-outside-init
    def setup(self):
        self.dPConnection = _dpcdlg.dPConnection(5)
        self.widget = _dpcdlg.doublePipeConnectionLengthDialog(self.dPConnection)

    def _testHelper(self, bot, value, button="okButton"):
        bot.addWidget(self.widget)
        self._clearAndWriteAndPressButton(bot, value, button)

    def _clearAndWriteAndPressButton(self, bot, value, button="okButton"):
        self.widget.lineEdit.clear()
        bot.keyClicks(self.widget.lineEdit, value)
        bot.mouseClick(getattr(self.widget, button), QtCore.Qt.LeftButton)

    def testDialogLineEdit(self, qtbot):
        self._testHelper(qtbot, "7")
        assert self.dPConnection.lengthInM == 7

    def testDialogCancel(self, qtbot):
        self._testHelper(qtbot, "7", button="cancelButton")
        assert self.dPConnection.lengthInM == 5

    def testDialogRaises(self, qtbot):
        with _m.patch('trnsysGUI.errors.showErrorMessageBox') as box:
            self._testHelper(qtbot, "-7")
            box.assert_called_with(errorMessage="Value must be positive.", title="Almost there")

    def testDialogInputAfterRaises(self, qtbot):
        with _m.patch('trnsysGUI.errors.showErrorMessageBox'):
            self._testHelper(qtbot, "-7")
            self._clearAndWriteAndPressButton(qtbot, "9")
            assert self.dPConnection.lengthInM == 9

    def teardown(self):
        self.widget.close()
