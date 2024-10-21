import pathlib as _pl
from collections import deque as _deque
import PyQt5.QtWidgets as _qtw


from trnsysGUI.constants import _CreateNewOrOpenExisting
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler
import trnsysGUI.common.cancelled as _ccl
import trnsysGUI.dialogs._UI_startupDialog_generated as _gen


class StartupDialog(_qtw.QDialog, _gen.Ui_startupDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.result = _ccl.CANCELLED
        self.buttonGroup.buttonClicked.connect(self.clickButtonHandler)
        self.listWidget.itemDoubleClicked.connect(self.clickButtonHandler)
        RecentProjectsHandler.initWithExistingRecentProjects()
        for recentProject in _deque(reversed(RecentProjectsHandler.recentProjects)):
            _qtw.QListWidgetItem(str(recentProject), self.listWidget)

    def clickButtonHandler(self, clickedItem):
        if clickedItem is self.cancelButton:
            self.result = _ccl.CANCELLED
            self.close()
        if clickedItem is self.createButton:
            self.result = _CreateNewOrOpenExisting.CREATE_NEW
            self.close()
        if clickedItem is self.openButton:
            self.result = _CreateNewOrOpenExisting.OPEN_EXISTING
            self.close()
        if isinstance(clickedItem, _qtw.QListWidgetItem):
            self.result = _pl.Path(clickedItem.text())
            self.close()

    @staticmethod
    def showDialogAndGetResult() -> _ccl.MaybeCancelled[_CreateNewOrOpenExisting | _pl.Path]:
        dialog = StartupDialog()
        dialog.exec()
        return dialog.result
