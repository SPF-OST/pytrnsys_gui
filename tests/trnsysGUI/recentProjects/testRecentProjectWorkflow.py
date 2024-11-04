from collections import deque as _deque

from PyQt5 import QtWidgets as _qtw

import pytrnsys.utils.log as _ulog
import trnsysGUI.common.cancelled as _ccl
import trnsysGUI.dialogs.startup.dialog as _sd
import trnsysGUI.mainWindow as mw
import trnsysGUI.messageBox as _mb
import trnsysGUI.project as _proj
import trnsysGUI.recentProjectsHandler as _rph
from .. import constants as _consts


class TestRecentProjectWorkflow:

    def testIfRecentProjectsAreShownInDialog(self, monkeypatch, qtbot):
        """Tests if the startup dialog displays recent projects as expected"""
        monkeypatch.setattr(
            _rph.RecentProjectsHandler,
            _rph.RecentProjectsHandler.initWithExistingRecentProjects.__name__,
            lambda: None,
        )

        _rph.RecentProjectsHandler.recentProjects = _deque(
            [
                _consts.PATH_TO_PROJECT_3,
                _consts.PATH_TO_PROJECT_2,
                _consts.PATH_TO_PROJECT_1,
            ]
        )
        startupDialog = _sd.StartupDialog()
        qtbot.addWidget(startupDialog)
        startupDialog.show()
        firstProjectInList = startupDialog.listWidget.item(0)
        secondProjectInList = startupDialog.listWidget.item(1)
        thirdProjectInList = startupDialog.listWidget.item(2)

        assert startupDialog.isVisible()
        assert (
            firstProjectInList.text()
            == f"{_consts.PATH_TO_PROJECT_3.stem} {_consts.PATH_TO_PROJECT_3}"
        )
        assert (
            secondProjectInList.text()
            == f"{_consts.PATH_TO_PROJECT_2.stem} {_consts.PATH_TO_PROJECT_2}"
        )
        assert (
            thirdProjectInList.text()
            == f"{_consts.PATH_TO_PROJECT_1.stem} {_consts.PATH_TO_PROJECT_1}"
        )

    def testIfRecenProjectsAreShownCorrectlyInMainWindow(
        self, monkeypatch, qtbot
    ):
        """Opens a recent project and makes sure recent project file menu is displayed correctly.
        Then opens another recent projects and checks if it's still display correctly
        """
        monkeypatch.setattr(
            _rph.RecentProjectsHandler,
            _rph.RecentProjectsHandler.initWithExistingRecentProjects.__name__,
            lambda: None,
        )
        monkeypatch.setattr(
            _rph.RecentProjectsHandler,
            _rph.RecentProjectsHandler.save.__name__,
            lambda: None,
        )
        monkeypatch.setattr(
            _mb.MessageBox,
            _mb.MessageBox.create.__name__,
            lambda messageText: _qtw.QMessageBox.Yes,
        )
        monkeypatch.setattr(
            _sd.StartupDialog,
            _sd.StartupDialog.showDialogAndGetResult.__name__,
            lambda: _consts.PATH_TO_PROJECT_1,
        )

        _rph.RecentProjectsHandler.recentProjects = _deque(
            [
                _consts.PATH_TO_PROJECT_3,
                _consts.PATH_TO_PROJECT_2,
                _consts.PATH_TO_PROJECT_1,
            ]
        )
        getProjectResult = _proj.getProject()
        logger = _ulog.getOrCreateCustomLogger("root", "INFO")
        mainWindow = mw.MainWindow(logger, _ccl.value(getProjectResult))
        qtbot.addWidget(mainWindow)
        mainWindow.showBoxOnClose = False

        mainWindow.show()
        action1 = mainWindow.recentProjectsMenu.actions()[0]
        action2 = mainWindow.recentProjectsMenu.actions()[1]

        assert mainWindow.isVisible()
        assert mainWindow.editor.isVisible()
        assert (
            action1.text()
            == f"{_consts.PATH_TO_PROJECT_3.stem} {_consts.PATH_TO_PROJECT_3}"
        )
        assert (
            action2.text()
            == f"{_consts.PATH_TO_PROJECT_2.stem} {_consts.PATH_TO_PROJECT_2}"
        )

        mainWindow.openRecentFile(action1)
        action1 = mainWindow.recentProjectsMenu.actions()[0]
        action2 = mainWindow.recentProjectsMenu.actions()[1]

        assert (
            action1.text()
            == f"{_consts.PATH_TO_PROJECT_1.stem} {_consts.PATH_TO_PROJECT_1}"
        )
        assert (
            action2.text()
            == f"{_consts.PATH_TO_PROJECT_2.stem} {_consts.PATH_TO_PROJECT_2}"
        )
