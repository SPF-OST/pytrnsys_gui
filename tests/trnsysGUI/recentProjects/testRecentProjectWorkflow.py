from collections import deque as _deque

import pytrnsys.utils.log as _ulog
from PyQt5 import QtWidgets as _qtw

import trnsysGUI.common.cancelled as _ccl
from tests.trnsysGUI.constants import PROJECT_1, PROJECT_2, PROJECT_3
from trnsysGUI.dialogs.startupDialog import StartupDialog
from trnsysGUI.mainWindow import MainWindow
from trnsysGUI.messageBox import MessageBox
from trnsysGUI.project import getProject
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler


class TestRecentProjectWorkflow:

    def testIfRecentProjectsAreShownInDialog(self, monkeypatch, qtbot):
        monkeypatch.setattr(
            RecentProjectsHandler, RecentProjectsHandler.initWithExistingRecentProjects.__name__, lambda: None
        )

        RecentProjectsHandler.recentProjects = _deque([PROJECT_1, PROJECT_2, PROJECT_3])
        startupDialog = StartupDialog()
        qtbot.addWidget(startupDialog)
        startupDialog.show()
        firstProjectInList = startupDialog.listWidget.item(0)
        secondProjectInList = startupDialog.listWidget.item(1)
        thirdProjectInList = startupDialog.listWidget.item(2)

        assert startupDialog.isVisible()
        assert firstProjectInList.text() == str(PROJECT_3)
        assert secondProjectInList.text() == str(PROJECT_2)
        assert thirdProjectInList.text() == str(PROJECT_1)

    def testIfRecenProjectsAreShownCorrectlyInMainWindow(self, monkeypatch, qtbot):
        monkeypatch.setattr(
            RecentProjectsHandler, RecentProjectsHandler.initWithExistingRecentProjects.__name__, lambda: None
        )
        monkeypatch.setattr(RecentProjectsHandler, RecentProjectsHandler.save.__name__, lambda: None)
        monkeypatch.setattr(MessageBox, MessageBox.create.__name__, lambda messageText: _qtw.QMessageBox.Yes)
        monkeypatch.setattr(StartupDialog, StartupDialog.showDialogAndGetResult.__name__, lambda: PROJECT_1)

        RecentProjectsHandler.recentProjects = _deque([PROJECT_1, PROJECT_2, PROJECT_3])
        getProjectResult = getProject()
        logger = _ulog.getOrCreateCustomLogger("root", "INFO")
        mainWindow = MainWindow(logger, _ccl.value(getProjectResult))
        qtbot.addWidget(mainWindow)
        mainWindow.showBoxOnClose = False

        mainWindow.show()
        action1 = mainWindow.recentProjectsMenu.actions()[0]
        action2 = mainWindow.recentProjectsMenu.actions()[1]

        assert mainWindow.isVisible()
        assert mainWindow.editor.isVisible()
        assert action1.text() == str(PROJECT_3)
        assert action2.text() == str(PROJECT_2)

        mainWindow.openRecentFile(action1)
        action1 = mainWindow.recentProjectsMenu.actions()[0]
        action2 = mainWindow.recentProjectsMenu.actions()[1]

        assert action1.text() == str(PROJECT_1)
        assert action2.text() == str(PROJECT_2)