import unittest.mock as _m

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import trnsysGUI.dialogs.connections.doublePipe as _dpcdlg
import trnsysGUI.warningsAndErrors as _werrors


_SHOW_ERROR_FUNCTION_NAME = (
    f"{_werrors.__name__}.{_werrors.showMessageBox.__name__}"
)


class TestDoublePipeConnectionPropertiesDialog:  # pylint: disable = attribute-defined-outside-init
    def setup(self):
        self.connectionModel = _dpcdlg.ConnectionModel(
            "TS_A", lengthInM=5, shallBeSimulated=False
        )
        self.dialog = _dpcdlg.DoublePipeConnectionPropertiesDialog(
            self.connectionModel
        )

    def _setLengthAndPressButton(
        self,
        bot,
        value,
        standardButton: _qtw.QDialogButtonBox.StandardButton = _qtw.QDialogButtonBox.Ok,
    ):
        bot.addWidget(self.dialog)
        self._clearAndWriteAndPressButton(bot, value, standardButton)

    def _clearAndWriteAndPressButton(
        self,
        bot,
        value,
        standardButton: _qtw.QDialogButtonBox.StandardButton = _qtw.QDialogButtonBox.Ok,
    ) -> None:
        bot.mouseClick(self.dialog.lengthInMLineEdit, _qtc.Qt.LeftButton)
        bot.keyClick(
            self.dialog.lengthInMLineEdit, "A", _qtc.Qt.ControlModifier
        )
        bot.keyClicks(self.dialog.lengthInMLineEdit, value)
        bot.keyClick(self.dialog.lengthInMLineEdit, _qtc.Qt.Key_Enter)

        button = self.dialog.buttonBox.button(standardButton)
        bot.mouseClick(button, _qtc.Qt.LeftButton)

    def testDialogLineEdit(self, qtbot):
        self._setLengthAndPressButton(qtbot, "7")
        assert self.connectionModel.lengthInM == 7

    def testDialogRaises(self, qtbot):
        with _m.patch(_SHOW_ERROR_FUNCTION_NAME) as box:
            self._setLengthAndPressButton(qtbot, "-7")
            box.assert_called_with(
                "Could not parse the length. Please make sure it's a non-negative number."
            )

    def testDialogInputAfterRaises(self, qtbot):
        with _m.patch(_SHOW_ERROR_FUNCTION_NAME):
            self._setLengthAndPressButton(qtbot, "-7")
            self._clearAndWriteAndPressButton(qtbot, "9")
            assert self.connectionModel.lengthInM == 9

    def teardown(self):
        self.dialog.close()
