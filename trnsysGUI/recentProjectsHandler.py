import pathlib as _pl
import typing as _tp
from collections import deque as _deque

from trnsysGUI import settings as _settings


class RecentProjectsHandler:

    NUMBER_OF_RECENT_PROJECTS = 15

    recentProjects: _tp.Deque[_pl.Path] = _deque(maxlen=NUMBER_OF_RECENT_PROJECTS)

    @classmethod
    def initWithExistingRecentProjects(cls):
        """Initialize the deque with recent projects saved in the settings.json"""
        cls.recentProjects.clear()
        recentProjectsFromFile = _settings.Settings.load().recentProjects
        cls.recentProjects.extend(_pl.Path(p) for p in recentProjectsFromFile)

    @classmethod
    def addProject(cls, projectToAdd: _pl.Path):
        """Add a project to the deque. If it already exists, move it to the most recent."""
        if projectToAdd in cls.recentProjects:
            cls.recentProjects.remove(projectToAdd)
        cls.recentProjects.appendleft(projectToAdd)
        cls.save()

    @classmethod
    def removeProject(cls, projectToRemove: _pl.Path):
        cls.recentProjects.remove(projectToRemove)
        cls.save()

    @classmethod
    def save(cls):
        validPathsToSave = _deque([p.as_posix() for p in cls.recentProjects])
        settings = _settings.Settings.load()
        settings.recentProjects = validPathsToSave
        settings.save()

    @classmethod
    def getLengthOfLongestFileName(cls) -> int:
        return max((len(recentProject.stem) for recentProject in cls.recentProjects), default=0)
