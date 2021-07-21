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
        ["TRIHP_dualSource", "HeatingNetwork", "ExternalHeatExchanger"]
    )
    def testExport(self, exampleProjectName: str):
        helper = _Helper(exampleProjectName)
        helper.setup()

        # The following line is required otherwise QT will crash
        _ = _qtw.QApplication([])

        projectFolderPath = helper.projectFolderPath
        self._exportHydraulic(projectFolderPath, _format="mfs")
        self._exportHydraulic(projectFolderPath, _format="ddck")

        helper.ensureActualProducedFilesAreAsExpected()

    @staticmethod
    def _exportHydraulic(projectFolderPath, *, _format):
        logger = _log.Logger("root")
        editor = _de.Editor(
            parent=None, projectFolder=str(projectFolderPath), jsonPath=None, loadValue="load", logger=logger
        )
        editor.exportHydraulics(exportTo=_format)


class _Helper:
    def __init__(self, exampleProjectName: str):
        self._exampleProjectName = exampleProjectName

        dataFolderPath = _pl.Path(__file__).parent / "data"

        self._actualFolderPath = dataFolderPath / "actual"

        self.projectFolderPath = self._actualFolderPath / self._exampleProjectName
        expectedProjectFolderPath = dataFolderPath / "expected" / self._exampleProjectName

        mfsDeckFileName = f"{self._exampleProjectName}_mfs.dck"
        self._actualMfsDckFile = self.projectFolderPath / mfsDeckFileName
        self._expectedMfsDckFile = expectedProjectFolderPath / mfsDeckFileName

        relativeHydraulicDdckPath = _pl.Path("ddck") / "hydraulic" / "hydraulic.ddck"
        self._actualHydraulicDckFile = self.projectFolderPath / relativeHydraulicDdckPath
        self._expectedHydraulicDckFile = expectedProjectFolderPath / relativeHydraulicDdckPath

    def setup(self):
        self._copyExampleToTestInputFolder()

    def ensureActualProducedFilesAreAsExpected(self):
        self._ensureFilesAreEqual(
            self._actualMfsDckFile, self._expectedMfsDckFile, shallReplaceRandomizedFlowRates=True
        )
        self._ensureFilesAreEqual(
            self._actualHydraulicDckFile, self._expectedHydraulicDckFile, shallReplaceRandomizedFlowRates=False
        )

    def _ensureFilesAreEqual(self, actualDeckFile, expectedDckFile, shallReplaceRandomizedFlowRates):
        actualContent = actualDeckFile.read_text()
        expectedContent = expectedDckFile.read_text()

        if shallReplaceRandomizedFlowRates:
            actualContent = self._replaceRandomizedFlowRatesWithPlaceHolder(
                actualContent, placeholder="XXX"
            )

        assert actualContent == expectedContent

    def _copyExampleToTestInputFolder(self):
        if self._actualFolderPath.exists():
            _sh.rmtree(self._actualFolderPath)

        pytrnsysGuiDir = _pl.Path(__file__).parents[3]
        exampleFolderPath = pytrnsysGuiDir / "data" / "examples" / self._exampleProjectName

        _sh.copytree(exampleFolderPath, self.projectFolderPath)

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
            return "MfrsupplyWater = 1000"

        variableName = match["variableName"]

        return f"{variableName} = {placeholder}"
