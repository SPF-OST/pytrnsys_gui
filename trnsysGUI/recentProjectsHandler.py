from collections import deque as _deque
import pathlib as _pl

from trnsysGUI import settings as _settings


class RecentProjectsHandler:
    recentProjects = list[_pl.Path]

    @classmethod
    def initWithExistingRecentProjects(cls):
        """Initialize the deque with recent projects saved in the settings.json"""
        recentProjectsFromFile = _settings.Settings.load().recentProjects
        cls.recentProjects = _deque([_pl.Path(p) for p in recentProjectsFromFile], maxlen=5)

    @classmethod
    def addProject(cls, projectToAdd: _pl.Path):
        """Add a project to the deque. If it already exists, move it to the most recent."""
        if projectToAdd in cls.recentProjects:
            cls.recentProjects.remove(projectToAdd)
        cls.recentProjects.append(projectToAdd)
        cls.save()

    @classmethod
    def save(cls):
        validPathsToSave = _deque([p.as_posix() for p in cls.recentProjects if p.exists()], maxlen=5)
        settings = _settings.Settings.load()
        settings.recentProjects = validPathsToSave
        settings.save()
