from collections import deque as _deque
from unittest.mock import patch
import pathlib as _pl

from trnsysGUI.recentProjectsHandler import RecentProjectsHandler
from tests.trnsysGUI.constants import PATH_TO_SETTINGS_JSON, PROJECT_1, PROJECT_2, PROJECT_3


class TestRecentProjectsHandler:

    @patch("trnsysGUI.settings.Settings._getSettingsFilePath")
    def testLoadRecentProjectsFromSettingsJson(self, mockGetSettingsFilePath):
        mockGetSettingsFilePath.return_value = _pl.Path(PATH_TO_SETTINGS_JSON).absolute()

        RecentProjectsHandler.initWithExistingRecentProjects()

        assert len(RecentProjectsHandler.recentProjects) == 3

    def testAddingRecentProject(self):
        RecentProjectsHandler.recentProjects = _deque(
            [
                PROJECT_1,
                PROJECT_2,
            ]
        )

        RecentProjectsHandler.addProject(PROJECT_3)

        assert len(RecentProjectsHandler.recentProjects) == 3

    def testAddingProjectThatAlreadyExists(self):
        RecentProjectsHandler.recentProjects = _deque(
            [
                PROJECT_1,
                PROJECT_2,
            ]
        )

        RecentProjectsHandler.addProject(PROJECT_1)

        assert len(RecentProjectsHandler.recentProjects) == 2
        assert RecentProjectsHandler.recentProjects[-1] == PROJECT_1
