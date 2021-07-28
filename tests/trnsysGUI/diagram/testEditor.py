import dataclasses as _dc
import logging as _log
import pathlib as _pl
import re as _re
import shutil as _sh
import typing as _tp

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import trnsysGUI.StorageTank as _st
import trnsysGUI.diagram.Editor as _de

_DATA_DIR = _pl.Path(__file__).parent / "data"


@_dc.dataclass
class _Project:
    projectName: str
    testCasesDirName: str
    shallCopyFolderFromExamples: bool

    @staticmethod
    def createForTestProject(projectName: str) -> "_Project":
        return _Project(projectName, "tests", False)

    @staticmethod
    def createForExampleProject(projectName: str) -> "_Project":
        return _Project(projectName, "examples", True)

    @property
    def testId(self) -> str:
        return f"{self.projectName} [in {self.testCasesDirName}]"


def getProjects() -> _tp.Iterable[_Project]:
    yield _Project.createForExampleProject("TRIHP_dualSource")

    yield from getTestProjects()


def getTestProjects() -> _tp.Iterable[_Project]:
    testProjectTestCasesDir = _DATA_DIR / "tests"
    testProjectTestCaseDirPaths = [tc for tc in testProjectTestCasesDir.iterdir() if not tc.name == "README.txt"]
    for testProjectTestCaseDirPath in testProjectTestCaseDirPaths:
        projectName = testProjectTestCaseDirPath.name
        yield _Project.createForTestProject(projectName)


TEST_CASES = [_pt.param(p, id=p.testId) for p in getProjects()]


class TestEditor:
    @_pt.mark.parametrize("project", TEST_CASES)
    def testStorageAndHydraulicExports(self, project: _Project, request: _pt.FixtureRequest):
        helper = _Helper(project)
        helper.setup()

        # The following line is required otherwise QT will crash
        application = _qtw.QApplication([])

        def quitApplication():
            application.quit()

        request.addfinalizer(quitApplication)

        projectFolderPath = helper.actualProjectFolderPath

        self._exportHydraulic(projectFolderPath, _format="mfs")
        mfsDdckRelativePath = f"{project.projectName}_mfs.dck"
        helper.ensureFilesAreEqual(mfsDdckRelativePath, shallReplaceRandomizedFlowRates=True)

        self._exportHydraulic(projectFolderPath, _format="ddck")
        hydraulicDdckRelativePath = "ddck/hydraulic/hydraulic.ddck"
        helper.ensureFilesAreEqual(hydraulicDdckRelativePath, shallReplaceRandomizedFlowRates=False)

        storageTanks = self._exportStorageTank(projectFolderPath)
        for storageTank in storageTanks:
            ddckFileRelativePath = f"ddck/{storageTank.displayName}/{storageTank.displayName}.ddck"
            helper.ensureFilesAreEqual(ddckFileRelativePath, shallReplaceRandomizedFlowRates=False)

            ddcxFileRelativePath = f"ddck/{storageTank.displayName}/{storageTank.displayName}.ddcx"
            helper.ensureFilesAreEqual(ddcxFileRelativePath, shallReplaceRandomizedFlowRates=False)

    def _exportStorageTank(self, projectFolderPath):
        editor = self._createEditor(projectFolderPath)
        storageTanks = [
            o
            for o in editor.trnsysObj
            if isinstance(o, _st.StorageTank)  # type: ignore[attr-defined] # pylint: disable=no-member
        ]
        for storageTank in storageTanks:
            storageTank.exportDck()
        return storageTanks

    @classmethod
    def _exportHydraulic(cls, projectFolderPath, *, _format):
        editor = cls._createEditor(projectFolderPath)
        editor.exportHydraulics(exportTo=_format)

    @staticmethod
    def _createEditor(projectFolderPath):
        logger = _log.Logger("root")
        editor = _de.Editor(
            parent=None,
            projectFolder=str(projectFolderPath),
            jsonPath=None,
            loadValue="load",
            logger=logger,
        )
        return editor


class _Helper:
    def __init__(
        self,
        project: _Project,
    ):
        self._project = project

        testCasesFolderPath = _DATA_DIR / self._project.testCasesDirName

        # project name is used twice because the project file must always be contained in a folder
        # of the same name
        self.actualProjectFolderPath = testCasesFolderPath / self._project.projectName / self._project.projectName

        self._expectedProjectFolderPath = testCasesFolderPath / self._project.projectName / "expected"

    def setup(self):
        if self._project.shallCopyFolderFromExamples:
            self._copyExampleToTestInputFolder()

    def ensureFilesAreEqual(self, fileRelativePathAsString: str, shallReplaceRandomizedFlowRates: bool):
        fileRelativePath = _pl.Path(fileRelativePathAsString)
        actualFilePath = self.actualProjectFolderPath / fileRelativePath
        expectedFilePath = self._expectedProjectFolderPath / fileRelativePath

        actualContent = actualFilePath.read_text()
        expectedContent = expectedFilePath.read_text()

        if shallReplaceRandomizedFlowRates:
            actualContent = self._replaceRandomizedFlowRatesWithPlaceHolder(actualContent, placeholder="XXX")

        assert actualContent == expectedContent

    def _copyExampleToTestInputFolder(self):
        if self.actualProjectFolderPath.exists():
            _sh.rmtree(self.actualProjectFolderPath)

        pytrnsysGuiDir = _pl.Path(__file__).parents[3]
        exampleFolderPath = pytrnsysGuiDir / "data" / "examples" / self._project.projectName

        _sh.copytree(exampleFolderPath, self.actualProjectFolderPath)

    @classmethod
    def _replaceRandomizedFlowRatesWithPlaceHolder(cls, actualContent, placeholder):
        pattern = r"^(?P<variableName>Mfr[^ \t=]+)[ \t]+=[ \t]+[0-9\.]+"

        def replaceValueWithPlaceHolder(match: _tp.Match):
            return cls._processMatch(match, placeholder)

        actualContent = _re.sub(pattern, replaceValueWithPlaceHolder, actualContent, flags=_re.MULTILINE)

        return actualContent

    @staticmethod
    def _processMatch(match: _tp.Match, placeholder: str) -> str:
        matchedText = match[0]
        if matchedText == "MfrsupplyWater = 1000":
            return matchedText

        variableName = match["variableName"]

        return f"{variableName} = {placeholder}"
