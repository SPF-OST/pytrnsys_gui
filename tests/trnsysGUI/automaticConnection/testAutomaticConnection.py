import dataclasses as _dc
import logging as _log
import pathlib as _pl
import typing as _tp

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import trnsysGUI.diagram.Editor as _de

_DATA_DIR_ = _pl.Path(__file__).parent / "data"


@_dc.dataclass
class _Project:
    projectName: str
    shallCopyFolderFromExamples: bool

    @staticmethod
    def createForProject(projectName: str) -> "_Project":
        return _Project(projectName, False)

    @property
    def testId(self) -> str:
        return f"{self.projectName}"


def getProjects(path: _pl.Path) -> _tp.Iterable[_Project]:
    for projectDirPath in path.iterdir():
        projectName = projectDirPath.name
        yield _Project.createForProject(projectName)


TEST_CASES = [_pt.param(p, id=p.testId) for p in getProjects(_DATA_DIR_)]


class TestAutomaticConnection:
    @_pt.mark.parametrize("project", TEST_CASES)
    def testConnectionJson(self, project: _Project, request: _pt.FixtureRequest):
        baseDirPath = _DATA_DIR_ / project.projectName / "base"
        expectedDirPath = _DATA_DIR_ / project.projectName / "expected"

        baseJsonFilePath = baseDirPath / "connection.json"
        expectedJsonFilePath = expectedDirPath / "connection.json"

        # The following line is required otherwise QT will crash
        application = _qtw.QApplication([])

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        editor = self._createEditor(baseDirPath)
        editor.exportJsonFile()

        with open(baseJsonFilePath, "r", encoding="utf8") as baseJsonFile, open(
                expectedJsonFilePath, "r", encoding="utf8") as expectedJsonFile:
            baseJsonText = baseJsonFile.read()
            expectedJsonText = expectedJsonFile.read()

        assert baseJsonText == expectedJsonText

    @staticmethod
    def _createEditor(projectFolderPath): # pylint: disable=duplicate-code
        logger = _log.Logger("root")
        editor = _de.Editor(
            parent=None,
            projectFolder=str(projectFolderPath),
            jsonPath=None,
            loadValue="load",
            logger=logger,
        )
        return editor
