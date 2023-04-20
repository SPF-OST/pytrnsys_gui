import dataclasses as _dc
import pathlib as _pl
import shutil as _su
import subprocess as _sp
import typing as _tp

import pandas as _pd

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
        self._project = project

        testCasesFolderPath = DATA_DIR / self._project.testCasesDirName

        # project name is used twice because the project file must always be contained in a folder
        # of the same name
        self.actualProjectFolderPath = testCasesFolderPath / self._project.projectName / self._project.projectName

        self._expectedProjectFolderPath = testCasesFolderPath / self._project.projectName / "expected"

    def setup(self):
        if self._project.exampleDirNameToCopyFrom:
            self._copyExampleToTestInputFolder()

        self._removeUntrackedPaths()

    def _removeUntrackedPaths(self):
        untrackedPaths = self._getUntrackedPathsInActualProjectFolder()

        for untrackedPath in untrackedPaths:
            if untrackedPath.is_dir():
                _su.rmtree(untrackedPath)
            else:
                untrackedPath.unlink()

    def _getUntrackedPathsInActualProjectFolder(self):
        projectFolderPathUnderVersionControl = self._getProjectFolderPathUnderVersionControl()

        untrackedRelativePaths = self._getUntrackedRelativePaths(projectFolderPathUnderVersionControl)

        untrackedAbsolutePaths = [self.actualProjectFolderPath / p for p in untrackedRelativePaths]

        return untrackedAbsolutePaths

    def _getProjectFolderPathUnderVersionControl(self):
        if self._project.exampleDirNameToCopyFrom:
            return self._getProjectFolderPathInExamplesDir()

        return self.actualProjectFolderPath

    def _getProjectFolderPathInExamplesDir(self):
        assert self._project.exampleDirNameToCopyFrom

        pytrnsysGuiDir = _pl.Path(__file__).parents[3]

        exampleProjectPath = (
            pytrnsysGuiDir / "data" / self._project.exampleDirNameToCopyFrom / self._project.projectName
        )

        return exampleProjectPath

    def _getUntrackedRelativePaths(self, projectFolderPathUnderVersionControl):
        untrackedPathsRelativeToRepoRoot = self._getUntrackedPathsRelativeToRepoRoot(
            projectFolderPathUnderVersionControl
        )

        repositoryRootDirPath = self._getRepositoryRootDirPath()

        untrackedAbsolutePaths = [repositoryRootDirPath / p for p in untrackedPathsRelativeToRepoRoot]

        untrackedRelativePaths = [p.relative_to(projectFolderPathUnderVersionControl) for p in untrackedAbsolutePaths]

        return untrackedRelativePaths

    @staticmethod
    def _getUntrackedPathsRelativeToRepoRoot(projectFolderPathUnderVersionControl):
        completedProcess = _sp.run(
            ["git", "status", "-unormal", "--porcelain", str(projectFolderPathUnderVersionControl)],
            check=True,
            text=True,
            capture_output=True,
        )

        statusesAndUntrackedPath = completedProcess.stdout.splitlines()

        untrackedPaths = []
        for statusAndUntrackedPath in statusesAndUntrackedPath:
            status, untrackedPath = statusAndUntrackedPath.split()

            modifiedStatus = "??"
            if status != modifiedStatus:
                continue

            untrackedPaths.append(untrackedPath)

        return untrackedPaths

    @staticmethod
    def _getRepositoryRootDirPath():
        completedProcess = _sp.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            capture_output=True,
        )

        repositoryRootDirPath = completedProcess.stdout.splitlines()[0]

        return _pl.Path(repositoryRootDirPath)

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

    def _getActualAndExpectedFilePath(self, fileRelativePathAsString):
        fileRelativePath = _pl.Path(fileRelativePathAsString)
        actualFilePath = self.actualProjectFolderPath / fileRelativePath
        expectedFilePath = self._expectedProjectFolderPath / fileRelativePath
        return actualFilePath, expectedFilePath

    def ensureCSVsAreEqual(self, fileRelativePathAsString: str, absoluteTolerance: float = 1e-10) -> None:
        actualFilePath, expectedFilePath = self._getActualAndExpectedFilePath(fileRelativePathAsString)

        actualDf: _pd.DataFrame = _pd.read_csv(actualFilePath, delim_whitespace=True)
        expectedDf: _pd.DataFrame = _pd.read_csv(expectedFilePath, delim_whitespace=True)

        assert actualDf.shape == expectedDf.shape

        actualColumns = "\n".join(sorted(actualDf.columns))  # pylint: disable=no-member
        expectedColumns = "\n".join(sorted(expectedDf.columns))  # pylint: disable=no-member

        assert actualColumns == expectedColumns

        maxAbsoluteDifference = (actualDf - expectedDf).max().max()

        assert maxAbsoluteDifference <= absoluteTolerance

    def _copyExampleToTestInputFolder(self):
        if self.actualProjectFolderPath.exists():
            _su.rmtree(self.actualProjectFolderPath)

        projectPathInExamplesDir = self._getProjectFolderPathInExamplesDir()

        _su.copytree(projectPathInExamplesDir, self.actualProjectFolderPath)
