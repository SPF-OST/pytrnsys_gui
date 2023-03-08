from PyQt5 import QtCore

import trnsysGUI.dialogs.connectionDialogs.doublePipeConnectionLengthDialog as _dpcdlg


def testDialogLineEdit(qtbot):
    container = _dpcdlg.LengthContainer(5)
    widget = _dpcdlg.doublePipeConnectionLengthDialog(container)
    qtbot.addWidget(widget)
    widget.lineEdit.clear()
    qtbot.keyClicks(widget.lineEdit, "7")

    qtbot.mouseClick(widget.okButton, QtCore.Qt.LeftButton)
    assert container.lengthInM == 7


def testDialogCancel(qtbot):
    container = _dpcdlg.LengthContainer(5)
    widget = _dpcdlg.doublePipeConnectionLengthDialog(container)
    qtbot.addWidget(widget)
    widget.lineEdit.clear()
    qtbot.keyClicks(widget.lineEdit, "7")

    qtbot.mouseClick(widget.cancelButton, QtCore.Qt.LeftButton)
    assert container.lengthInM == 5


def testDialogExit(qtbot):
    container = _dpcdlg.LengthContainer(5)
    widget = _dpcdlg.doublePipeConnectionLengthDialog(container)
    qtbot.addWidget(widget)
    widget.lineEdit.clear()
    qtbot.keyClicks(widget.lineEdit, "7")

    qtbot.mouseClick(widget.cancelButton, QtCore.Qt.LeftButton)
    assert container.lengthInM == 5


def testDialogRaises(qtbot):
    container = _dpcdlg.LengthContainer(5)
    widget = _dpcdlg.doublePipeConnectionLengthDialog(container)
    qtbot.addWidget(widget)
    widget.lineEdit.clear()
    qtbot.keyClicks(widget.lineEdit, "-7")

    qtbot.mouseClick(widget.cancelButton, QtCore.Qt.LeftButton)
    assert container.lengthInM == 5
