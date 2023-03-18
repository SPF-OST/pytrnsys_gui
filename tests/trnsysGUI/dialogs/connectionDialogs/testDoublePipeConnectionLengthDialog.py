import unittest.mock as _m
import pytest as _pt

from PyQt5 import QtCore, QtTest
from PyQt5 import QtWidgets as _widgets

import trnsysGUI.dialogs.connectionDialogs.doublePipeConnectionLengthDialog as _dpcdlg


class TestDoublePipeConnectionLengthDialog:  # pylint: disable = attribute-defined-outside-init
    def setup(self):
        self.widget = None
        self.dPConnection = None

    def _initializeDialog(self):
        self.dPConnection = _dpcdlg.DPConnection(5)
        self.widget = _dpcdlg.DoublePipeConnectionLengthDialog(self.dPConnection)

    @staticmethod
    def _applicationHandling(request):
        application = _widgets.QApplication([])

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

    def _testHelper(self, value, button="okButton"):
        # bot.addWidget(self.widget)
        self._clearAndWriteAndPressButton(value, button)

    def _clearAndWriteAndPressButton(self, value, button="okButton"):
        self.widget.lineEdit.clear()
        QtTest.QTest.keyClicks(self.widget.lineEdit, value)
        QtTest.QTest.mouseClick(getattr(self.widget, button), QtCore.Qt.LeftButton)

    def testDialogLineEdit(self, request: _pt.FixtureRequest):
        self._applicationHandling(request)
        self._initializeDialog()
        self._testHelper("7")
        assert self.dPConnection.lengthInM == 7

    def testDialogCancel(self, request: _pt.FixtureRequest):
        self._applicationHandling(request)
        self._initializeDialog()
        self._testHelper("7", button="cancelButton")
        assert self.dPConnection.lengthInM == 5

    def testDialogRaises(self, request: _pt.FixtureRequest):
        self._applicationHandling(request)
        self._initializeDialog()

        with _m.patch("trnsysGUI.errors.showErrorMessageBox") as box:
            self._testHelper("-7")
            box.assert_called_with(errorMessage="Value must be positive.", title="Almost there")

    def testDialogInputAfterRaises(self, request: _pt.FixtureRequest):
        self._applicationHandling(request)
        self._initializeDialog()
        with _m.patch("trnsysGUI.errors.showErrorMessageBox"):
            self._testHelper("-7")
            self._clearAndWriteAndPressButton("9")
            assert self.dPConnection.lengthInM == 9
