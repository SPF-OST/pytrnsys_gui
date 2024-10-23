from collections import deque as _deque

import pytrnsys.utils.log as _ulog
from PyQt5 import QtWidgets as _qtw

import trnsysGUI.common.cancelled as _ccl
import trnsysGUI.mainWindow as mw
from tests.trnsysGUI import constants
from trnsysGUI.dialogs.startupDialog import StartupDialog
from trnsysGUI.messageBox import MessageBox
from trnsysGUI.project import getProject
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler


class TestRecentProjectWorkflow:

    def testIfRecentProjectsAreShownInDialog(self, monkeypatch, qtbot):
        """Tests if the startup dialog displays recent projects as expected"""
        monkeypatch.setattr(
            RecentProjectsHandler, RecentProjectsHandler.initWithExistingRecentProjects.__name__, lambda: None
        )

        RecentProjectsHandler.recentProjects = _deque(
            [constants.PATH_TO_PROJECT_3, constants.PATH_TO_PROJECT_2, constants.PATH_TO_PROJECT_1]
        )
        startupDialog = StartupDialog()
        qtbot.addWidget(startupDialog)
        startupDialog.show()
        firstProjectInList = startupDialog.listWidget.item(0)
        secondProjectInList = startupDialog.listWidget.item(1)
        thirdProjectInList = startupDialog.listWidget.item(2)

        assert startupDialog.isVisible()
        assert firstProjectInList.text() == f"{constants.PATH_TO_PROJECT_3.stem} {constants.PATH_TO_PROJECT_3}"
        assert secondProjectInList.text() == f"{constants.PATH_TO_PROJECT_2.stem} {constants.PATH_TO_PROJECT_2}"
        assert thirdProjectInList.text() == f"{constants.PATH_TO_PROJECT_1.stem} {constants.PATH_TO_PROJECT_1}"

    def testIfRecenProjectsAreShownCorrectlyInMainWindow(self, monkeypatch, qtbot):
        """Opens a recent project and makes sure recent project file menu is displayed correctly.
        Then opens another recent projects and checks if it's still display correctly"""
        monkeypatch.setattr(
            RecentProjectsHandler, RecentProjectsHandler.initWithExistingRecentProjects.__name__, lambda: None
        )
        monkeypatch.setattr(RecentProjectsHandler, RecentProjectsHandler.save.__name__, lambda: None)
        monkeypatch.setattr(MessageBox, MessageBox.create.__name__, lambda messageText: _qtw.QMessageBox.Yes)
        monkeypatch.setattr(
            StartupDialog, StartupDialog.showDialogAndGetResult.__name__, lambda: constants.PATH_TO_PROJECT_1
        )

        RecentProjectsHandler.recentProjects = _deque(
            [constants.PATH_TO_PROJECT_3, constants.PATH_TO_PROJECT_2, constants.PATH_TO_PROJECT_1]
        )
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
        assert action1.text() == f"{constants.PATH_TO_PROJECT_3.stem} {constants.PATH_TO_PROJECT_3}"
        assert action2.text() == f"{constants.PATH_TO_PROJECT_2.stem} {constants.PATH_TO_PROJECT_2}"

        mainWindow.openRecentFile(action1)
        action1 = mainWindow.recentProjectsMenu.actions()[0]
        action2 = mainWindow.recentProjectsMenu.actions()[1]

        assert action1.text() == f"{constants.PATH_TO_PROJECT_1.stem} {constants.PATH_TO_PROJECT_1}"
        assert action2.text() == f"{constants.PATH_TO_PROJECT_2.stem} {constants.PATH_TO_PROJECT_2}"
