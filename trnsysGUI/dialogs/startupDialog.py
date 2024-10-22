import pathlib as _pl

import PyQt5.QtWidgets as _qtw

import trnsysGUI.common.cancelled as _ccl
import trnsysGUI.dialogs._UI_startupDialog_generated as _gen
from trnsysGUI.constants import _CreateNewOrOpenExisting
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler


class StartupDialog(_qtw.QDialog, _gen.Ui_startupDialog):
    signal: _ccl.MaybeCancelled[_CreateNewOrOpenExisting | _pl.Path]

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.buttonGroup.buttonClicked.connect(self.clickButtonHandler)
        self.listWidget.itemDoubleClicked.connect(self.clickButtonHandler)
        RecentProjectsHandler.initWithExistingRecentProjects()
        for recentProject in RecentProjectsHandler.recentProjects:
            _qtw.QListWidgetItem(str(recentProject), self.listWidget)

    def clickButtonHandler(self, clickedItem):
        if clickedItem is self.cancelButton:
            self.signal = _ccl.CANCELLED
        if clickedItem is self.createButton:
            self.signal = _CreateNewOrOpenExisting.CREATE_NEW
        if clickedItem is self.openButton:
            self.signal = _CreateNewOrOpenExisting.OPEN_EXISTING
        if isinstance(clickedItem, _qtw.QListWidgetItem):
            self.signal = _pl.Path(clickedItem.text())
        self.close()

    @staticmethod
    def showDialogAndGetResult() -> _ccl.MaybeCancelled[_CreateNewOrOpenExisting | _pl.Path]:
        dialog = StartupDialog()
        dialog.exec()
        return dialog.signal
