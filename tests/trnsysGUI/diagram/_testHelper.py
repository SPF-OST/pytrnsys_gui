import dataclasses as _dc
import pathlib as _pl
import shutil as _su
import typing as _tp

import pandas as _pd

from . import _git

DATA_DIR = _pl.Path(__file__).parent / "data"


@_dc.dataclass
class Project:
    projectName: str
    testCasesDirName: str
    exampleDirNameToCopyFrom: _tp.Optional[str] = None

    @staticmethod
    def createForTestProject(projectName: str) -> "Project":
        return Project(projectName, "tests")

    @staticmethod
    def createForExampleProject(projectName: str, exampleDirNameToCopyFrom: str = "examples") -> "Project":
        return Project(projectName, "examples", exampleDirNameToCopyFrom)

    @property
    def testId(self) -> str:
        return f"{self.testCasesDirName}/{self.projectName}"


class Helper:
    def __init__(
        self,
        project: Project,
    ):
        self._projectFolderPathInExamplesDir = self._getProjectFolderPathInExamplesDir(project)

        testCasesFolderPath = DATA_DIR / project.testCasesDirName

        # project name is used twice because the project file must always be contained in a folder
        # of the same name
        self.actualProjectFolderPath = testCasesFolderPath / project.projectName / project.projectName

        self.expectedProjectFolderPath = testCasesFolderPath / project.projectName / "expected"

    @staticmethod
    def _getProjectFolderPathInExamplesDir(project: Project) -> _tp.Optional[_pl.Path]:
        if not project.exampleDirNameToCopyFrom:
            return None

        pytrnsysGuiDir = _pl.Path(__file__).parents[3]

        exampleProjectPath = pytrnsysGuiDir / "data" / project.exampleDirNameToCopyFrom / project.projectName

        return exampleProjectPath

    def setup(self) -> None:
        self._copyExampleToTestInputFolderIfNeeded()
        self._removeUntrackedPaths()

    def _removeUntrackedPaths(self) -> None:
        untrackedPaths = self._getUntrackedPathsInActualProjectFolder()

        for untrackedPath in untrackedPaths:
            if untrackedPath.is_dir():
                _su.rmtree(untrackedPath)
            else:
                untrackedPath.unlink()

    def _getUntrackedPathsInActualProjectFolder(self) -> _tp.Sequence[_pl.Path]:
        projectFolderPathUnderVersionControl = self._getProjectFolderPathUnderVersionControl()

        untrackedRelativePaths = _git.getUntrackedRelativePaths(projectFolderPathUnderVersionControl)

        untrackedAbsolutePaths = [self.actualProjectFolderPath / p for p in untrackedRelativePaths]

        return untrackedAbsolutePaths

    def _getProjectFolderPathUnderVersionControl(self) -> _pl.Path:
        return self._projectFolderPathInExamplesDir or self.actualProjectFolderPath

    def ensureFilesAreEqual(
        self, fileRelativePathAsString: str, replaceInExpected: _tp.Optional[_tp.Tuple[str, str]] = None
    ) -> None:
        actualFilePath, expectedFilePath = self._getActualAndExpectedFilePath(fileRelativePathAsString)

        actualContent = actualFilePath.read_text()

        expectedContent = expectedFilePath.read_text(encoding="windows-1252")
        if replaceInExpected:
            old, new = replaceInExpected
            expectedContent = expectedContent.replace(old, new)

        assert actualContent == expectedContent

    def _getActualAndExpectedFilePath(self, fileRelativePathAsString: str) -> _tp.Tuple[_pl.Path, _pl.Path]:
        fileRelativePath = _pl.Path(fileRelativePathAsString)
        actualFilePath = self.actualProjectFolderPath / fileRelativePath
        expectedFilePath = self.expectedProjectFolderPath / fileRelativePath
        return actualFilePath, expectedFilePath

    def ensureDataFramesAreEqual(self, fileRelativePathAsString: str) -> None:
        actualFilePath, expectedFilePath = self._getActualAndExpectedFilePath(fileRelativePathAsString)

        actualDf: _pd.DataFrame = _pd.read_csv(actualFilePath, delim_whitespace=True)
        expectedDf: _pd.DataFrame = _pd.read_csv(expectedFilePath, delim_whitespace=True)

        _pd.testing.assert_frame_equal(actualDf, expectedDf, atol=1e-10)

    def _copyExampleToTestInputFolderIfNeeded(self) -> None:
        if not self._projectFolderPathInExamplesDir:
            return

        if self.actualProjectFolderPath.exists():
            _su.rmtree(self.actualProjectFolderPath)

        _su.copytree(self._projectFolderPathInExamplesDir, self.actualProjectFolderPath)