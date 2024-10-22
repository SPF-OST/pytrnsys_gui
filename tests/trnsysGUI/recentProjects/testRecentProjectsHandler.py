import pathlib as _pl
from collections import deque as _deque

import trnsysGUI.recentProjectsHandler as rph
import trnsysGUI.settings as ting
from tests.trnsysGUI.constants import PATH_TO_SETTINGS_JSON, PROJECT_1, PROJECT_2, PROJECT_3


class TestRecentProjectsHandler:

    def testAddingRecentProject(self, monkeypatch):
        monkeypatch.setattr(rph.RecentProjectsHandler, rph.RecentProjectsHandler.save.__name__, lambda: None)
        rph.RecentProjectsHandler.recentProjects = _deque(
            [
                PROJECT_2,
                PROJECT_1,
            ]
        )

        rph.RecentProjectsHandler.addProject(PROJECT_3)

        assert len(rph.RecentProjectsHandler.recentProjects) == 3

    def testAddingProjectThatAlreadyExists(self, monkeypatch):
        monkeypatch.setattr(rph.RecentProjectsHandler, rph.RecentProjectsHandler.save.__name__, lambda: None)
        rph.RecentProjectsHandler.recentProjects = _deque(
            [
                PROJECT_2,
                PROJECT_1,
            ]
        )

        rph.RecentProjectsHandler.addProject(PROJECT_1)

        assert len(rph.RecentProjectsHandler.recentProjects) == 2
        assert rph.RecentProjectsHandler.recentProjects[0] == PROJECT_1

    def testLoadRecentProjectsFromSettingsJson(self, monkeypatch):
        """At the end to make sure, that no interaction with other tests occurs."""
        monkeypatch.setattr(
            ting.Settings,
            ting.Settings._getSettingsFilePath.__name__,  # pylint: disable=protected-access
            lambda: _pl.Path(PATH_TO_SETTINGS_JSON).absolute(),
        )

        rph.RecentProjectsHandler.initWithExistingRecentProjects()

        assert len(rph.RecentProjectsHandler.recentProjects) == 3
