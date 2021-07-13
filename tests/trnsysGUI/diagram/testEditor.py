import logging as _log
import pathlib as _pl
import shutil as _sh
import re as _re
import typing as _tp

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import trnsysGUI.diagram.Editor as _de


class TestEditor:
    @_pt.mark.parametrize(
        "exampleProjectName",
        ["TRIHP_dualSource", "HeatingNetwork"]
    )
    def testExportForMassFlowSolver(self, exampleProjectName: str):
        helper = _Helper(exampleProjectName)
        helper.setup()

        # The following line is required otherwise QT will crash
        _ = _qtw.QApplication([])

        logger = _log.Logger("root")
        editor = _de.Editor(
            parent=None, projectFolder=str(helper.projectFolderPath), jsonPath=None, loadValue="load", logger=logger
        )
        editor.exportData(exportTo="mfs")

        helper.ensureDckFilesAreEqualIgnoringRandomizedFlowRateValues()


class _Helper:
    def __init__(self, exampleProjectName: str):
        self._exampleProjectName = exampleProjectName

        dataFolderPath = _pl.Path(__file__).parent / "data"

        self._actualFolderPath = dataFolderPath / "actual"

        self.projectFolderPath = self._actualFolderPath / self._exampleProjectName
        expectedProjectFolderPath = dataFolderPath / "expected" / self._exampleProjectName

        deckFileName = f"{self._exampleProjectName}_mfs.dck"
        self._actualDckFile = self.projectFolderPath / deckFileName
        self._expectedDckFile = expectedProjectFolderPath / deckFileName

    def setup(self):
        self._copyExampleToTestInputFolder()

    def ensureDckFilesAreEqualIgnoringRandomizedFlowRateValues(self):
        actualContent = self._actualDckFile.read_text()
        expectedContent = self._expectedDckFile.read_text()

        actualContentWithoutRandomizedValues = self._replaceRandomizedMassflowRatesWithPlaceHolder(
            actualContent, placeholder="XXX"
        )

        assert actualContentWithoutRandomizedValues == expectedContent

    def _copyExampleToTestInputFolder(self):
        if self._actualFolderPath.exists():
            _sh.rmtree(self._actualFolderPath)

        pytrnsysGuiDir = _pl.Path(__file__).parents[3]
        exampleFolderPath = pytrnsysGuiDir / "data" / "examples" / self._exampleProjectName

        _sh.copytree(exampleFolderPath, self.projectFolderPath)

    @classmethod
    def _replaceRandomizedMassflowRatesWithPlaceHolder(cls, actualContent, placeholder):
        pattern = rf"^(?P<variableName>Mfr[^ \t=]+)[ \t]+=[ \t]+[0-9\.]+"

        def replaceValueWithPlaceHolder(match: _tp.Match):
            return cls._processMatch(match, placeholder)

        actualContent = _re.sub(pattern, replaceValueWithPlaceHolder, actualContent, flags=_re.MULTILINE)

        return actualContent

    @staticmethod
    def _processMatch(match: _tp.Match, placeholder: str) -> str:
        matchedText = match[0]
        if matchedText == "MfrsupplyWater = 1000":
            return "MfrsupplyWater = 1000"

        variableName = match["variableName"]

        return f"{variableName} = {placeholder}"
