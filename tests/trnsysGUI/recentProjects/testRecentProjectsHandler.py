import pathlib as _pl
from collections import deque as _deque

from tests.trnsysGUI.constants import PATH_TO_SETTINGS_JSON, PROJECT_1, PROJECT_2, PROJECT_3
from trnsysGUI.recentProjectsHandler import RecentProjectsHandler
from trnsysGUI.settings import Settings


class TestRecentProjectsHandler:

    def testLoadRecentProjectsFromSettingsJson(self, monkeypatch):
        monkeypatch.setattr(
            Settings,
            Settings._getSettingsFilePath.__name__,  # pylint: disable=protected-access
            lambda: _pl.Path(PATH_TO_SETTINGS_JSON).absolute(),
        )

        RecentProjectsHandler.initWithExistingRecentProjects()

        assert len(RecentProjectsHandler.recentProjects) == 3

    def testAddingRecentProject(self, monkeypatch):
        monkeypatch.setattr(RecentProjectsHandler, RecentProjectsHandler.save.__name__, lambda: None)
        RecentProjectsHandler.recentProjects = _deque(
            [
                PROJECT_2,
                PROJECT_1,
            ]
        )

        RecentProjectsHandler.addProject(PROJECT_3)

        assert len(RecentProjectsHandler.recentProjects) == 3

    def testAddingProjectThatAlreadyExists(self, monkeypatch):
        monkeypatch.setattr(RecentProjectsHandler, RecentProjectsHandler.save.__name__, lambda: None)
        RecentProjectsHandler.recentProjects = _deque(
            [
                PROJECT_2,
                PROJECT_1,
            ]
        )

        RecentProjectsHandler.addProject(PROJECT_1)

        assert len(RecentProjectsHandler.recentProjects) == 2
        assert RecentProjectsHandler.recentProjects[0] == PROJECT_1
