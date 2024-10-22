from collections import deque as _deque
import pytrnsys.utils.log as _ulog
from PyQt5 import QtWidgets as _qtw

import trnsysGUI.common.cancelled as _ccl
from tests.trnsysGUI import constants
from trnsysGUI.dialogs.startupDialog import StartupDialog
import trnsysGUI.mainWindow as mw
from trnsysGUI.messageBox import MessageBox
from trnsysGUI.project import getProject
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler


class TestRecentProjectWorkflow:

    def testIfRecentProjectsAreShownInDialog(self, monkeypatch, qtbot):
        monkeypatch.setattr(
            RecentProjectsHandler, RecentProjectsHandler.initWithExistingRecentProjects.__name__, lambda: None
        )

        RecentProjectsHandler.recentProjects = _deque([constants.PROJECT_3, constants.PROJECT_2, constants.PROJECT_1])
        startupDialog = StartupDialog()
        qtbot.addWidget(startupDialog)
        startupDialog.show()
        firstProjectInList = startupDialog.listWidget.item(0)
        secondProjectInList = startupDialog.listWidget.item(1)
        thirdProjectInList = startupDialog.listWidget.item(2)

        assert startupDialog.isVisible()
        assert firstProjectInList.text() == str(constants.PROJECT_3)
        assert secondProjectInList.text() == str(constants.PROJECT_2)
        assert thirdProjectInList.text() == str(constants.PROJECT_1)

    def testIfRecenProjectsAreShownCorrectlyInMainWindow(self, monkeypatch, qtbot):
        monkeypatch.setattr(
            RecentProjectsHandler, RecentProjectsHandler.initWithExistingRecentProjects.__name__, lambda: None
        )
        monkeypatch.setattr(RecentProjectsHandler, RecentProjectsHandler.save.__name__, lambda: None)
        monkeypatch.setattr(MessageBox, MessageBox.create.__name__, lambda messageText: _qtw.QMessageBox.Yes)
        monkeypatch.setattr(StartupDialog, StartupDialog.showDialogAndGetResult.__name__, lambda: constants.PROJECT_1)

        RecentProjectsHandler.recentProjects = _deque([constants.PROJECT_3, constants.PROJECT_2, constants.PROJECT_1])
        getProjectResult = getProject()
        logger = _ulog.getOrCreateCustomLogger("root", "INFO")
        mainWindow = mw.MainWindow(logger, _ccl.value(getProjectResult))
        qtbot.addWidget(mainWindow)
        mainWindow.showBoxOnClose = False

        mainWindow.show()
        action1 = mainWindow.recentProjectsMenu.actions()[0]
        action2 = mainWindow.recentProjectsMenu.actions()[1]

        assert mainWindow.isVisible()
        assert mainWindow.editor.isVisible()
        assert action1.text() == str(constants.PROJECT_3)
        assert action2.text() == str(constants.PROJECT_2)

        mainWindow.openRecentFile(action1)
        action1 = mainWindow.recentProjectsMenu.actions()[0]
        action2 = mainWindow.recentProjectsMenu.actions()[1]

        assert action1.text() == str(constants.PROJECT_1)
        assert action2.text() == str(constants.PROJECT_2)
