from collections import deque as _deque

import PyQt5.QtCore as _qtc
import PyQt5.QtWidgets as _qtw

import trnsysGUI.dialogs.startup.dialog as _sd
import trnsysGUI.recentProjectsHandler as _rph

from .. import constants as _consts


class TestStartupDialog:
    def testStartupDialogRecentSetup(self, monkeypatch, qtbot):
        monkeypatch.setattr(
            _rph.RecentProjectsHandler,
            _rph.RecentProjectsHandler.initWithExistingRecentProjects.__name__,
            lambda: None,
        )
        _rph.RecentProjectsHandler.recentProjects = _deque(
            [
                _consts.PATH_TO_PROJECT_1,
                _consts.PATH_TO_PROJECT_2,
                _consts.PATH_TO_PROJECT_3,
            ]
        )
        startupDialog = _sd.StartupDialog()
        qtbot.addWidget(startupDialog)
        recentClicked = _qtw.QListWidgetItem(
            f"{_consts.PATH_TO_PROJECT_1.stem}: {_consts.PATH_TO_PROJECT_1}"
        )
        recentClicked.setData(_qtc.Qt.UserRole, _consts.PATH_TO_PROJECT_1)

        startupDialog.clickButtonHandler(recentClicked)

        assert startupDialog.signal == _consts.PATH_TO_PROJECT_1
        assert startupDialog.listWidget.count() == 3
