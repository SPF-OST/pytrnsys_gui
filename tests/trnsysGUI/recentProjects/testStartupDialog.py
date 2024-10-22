from collections import deque as _deque
from PyQt5.QtWidgets import QListWidgetItem

from tests.trnsysGUI.constants import PROJECT_1, PROJECT_2, PROJECT_3
from trnsysGUI.dialogs.startupDialog import StartupDialog
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler


class TestStartupDialog:

    def testStartupDialogRecentSetup(self, monkeypatch, qtbot):
        monkeypatch.setattr(
            RecentProjectsHandler, RecentProjectsHandler.initWithExistingRecentProjects.__name__, lambda: None
        )
        RecentProjectsHandler.recentProjects = _deque([PROJECT_1, PROJECT_2, PROJECT_3])
        startupDialog = StartupDialog()
        qtbot.addWidget(startupDialog)
        recentClicked = QListWidgetItem(str(PROJECT_1))

        startupDialog.clickButtonHandler(recentClicked)

        assert startupDialog.signal == PROJECT_1
        assert startupDialog.listWidget.count() == 3
