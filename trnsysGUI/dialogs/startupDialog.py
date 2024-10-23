import pathlib as _pl

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
import PyQt5.QtWidgets as _qtw

import trnsysGUI.common.cancelled as _ccl
import trnsysGUI.dialogs._UI_startupDialog_generated as _gen
from trnsysGUI import constants
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler


class StartupDialog(_qtw.QDialog, _gen.Ui_startupDialog):
    signal: _ccl.MaybeCancelled[constants.CreateNewOrOpenExisting | _pl.Path]

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.buttonGroup.buttonClicked.connect(self.clickButtonHandler)
        self.listWidget.setFont(_qtg.QFont(constants.DEFAULT_MONOSPACED_FONT))
        self.listWidget.itemDoubleClicked.connect(self.clickButtonHandler)
        RecentProjectsHandler.initWithExistingRecentProjects()
        maxLength = RecentProjectsHandler.getLenghtOfLongestFileName()
        for recentProject in RecentProjectsHandler.recentProjects:
            formattedFileName = recentProject.stem.ljust(maxLength)
            _qtw.QListWidgetItem(f"{formattedFileName}: {recentProject}", self.listWidget).setData(
                _qtc.Qt.UserRole, recentProject
            )

    def clickButtonHandler(self, clickedItem):
        if clickedItem is self.cancelButton:
            self.signal = _ccl.CANCELLED
        if clickedItem is self.createButton:
            self.signal = constants.CreateNewOrOpenExisting.CREATE_NEW
        if clickedItem is self.openButton:
            self.signal = constants.CreateNewOrOpenExisting.OPEN_EXISTING
        if isinstance(clickedItem, _qtw.QListWidgetItem):
            self.signal = clickedItem.data(_qtc.Qt.UserRole)
        self.close()

    @staticmethod
    def showDialogAndGetResult() -> _ccl.MaybeCancelled[constants.CreateNewOrOpenExisting | _pl.Path]:
        dialog = StartupDialog()
        dialog.exec()
        return dialog.signal
