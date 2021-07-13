import logging as _log
import pathlib as _pl
import shutil as _sh
import re as _re
import typing as _tp

import PyQt5.QtWidgets as _qtw
import pytest as _pt

import trnsysGUI.diagram.Editor as _de
import trnsysGUI.StorageTank as _st


class TestEditor:
    @_pt.mark.parametrize(
        "exampleProjectName",
        ["TRIHP_dualSource", "HeatingNetwork", "ExternalHeatExchanger"],
    )
    def testStorageAndHydraulicExports(self, exampleProjectName: str):
        helper = _Helper(exampleProjectName)
        helper.setup()

        # The following line is required otherwise QT will crash
        _ = _qtw.QApplication([])

        projectFolderPath = helper.projectFolderPath
        self._exportHydraulic(projectFolderPath, _format="mfs")
        self._exportHydraulic(projectFolderPath, _format="ddck")

        editor = self._createEditor(projectFolderPath)
        storageTanks = [
            o
            for o in editor.trnsysObj
            if isinstance(o, _st.StorageTank)  # type: ignore[attr-defined] # pylint: disable=no-member
        ]
        for storageTank in storageTanks:
            storageTank.exportDck()

        mfsDckFileRelativePath = f"{exampleProjectName}_mfs.dck"
        helper.ensureFilesAreEqual(
            mfsDckFileRelativePath, shallReplaceRandomizedFlowRates=True
        )

        hydraulicDdckRelativePath = "ddck/hydraulic/hydraulic.ddck"
        helper.ensureFilesAreEqual(
            hydraulicDdckRelativePath, shallReplaceRandomizedFlowRates=False
        )

        for storageTank in storageTanks:
            ddckFileRelativePath = (
                f"ddck/{storageTank.displayName}/{storageTank.displayName}.ddck"
            )
            helper.ensureFilesAreEqual(
                ddckFileRelativePath, shallReplaceRandomizedFlowRates=False
            )

            ddcxFileRelativePath = (
                f"ddck/{storageTank.displayName}/{storageTank.displayName}.ddcx"
            )
            helper.ensureFilesAreEqual(
                ddcxFileRelativePath, shallReplaceRandomizedFlowRates=False
            )

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
        exampleProjectName: str,
    ):
        self._exampleProjectName = exampleProjectName

        dataFolderPath = _pl.Path(__file__).parent / "data"

        self._actualFolderPath = dataFolderPath / "actual"

        self.projectFolderPath = self._actualFolderPath / self._exampleProjectName
        self._expectedProjectFolderPath = (
            dataFolderPath / "expected" / self._exampleProjectName
        )

    def setup(self):
        self._copyExampleToTestInputFolder()

    def ensureFilesAreEqual(
        self,
        fileToCompareRelativePathAsString: str,
        shallReplaceRandomizedFlowRates: bool,
    ):
        fileToCompareRelativePath = _pl.Path(fileToCompareRelativePathAsString)

        actualFilePath = self.projectFolderPath / fileToCompareRelativePath
        expectedFilePath = self._expectedProjectFolderPath / fileToCompareRelativePath

        actualContent = actualFilePath.read_text()
        expectedContent = expectedFilePath.read_text()

        if shallReplaceRandomizedFlowRates:
            actualContent = self._replaceRandomizedFlowRatesWithPlaceHolder(
                actualContent, placeholder="XXX"
            )

        assert actualContent == expectedContent

    def _copyExampleToTestInputFolder(self):
        if self._actualFolderPath.exists():
            _sh.rmtree(self._actualFolderPath)

        pytrnsysGuiDir = _pl.Path(__file__).parents[3]
        exampleFolderPath = (
            pytrnsysGuiDir / "data" / "examples" / self._exampleProjectName
        )

        _sh.copytree(exampleFolderPath, self.projectFolderPath)

    @classmethod
    def _replaceRandomizedFlowRatesWithPlaceHolder(cls, actualContent, placeholder):
        pattern = r"^(?P<variableName>Mfr[^ \t=]+)[ \t]+=[ \t]+[0-9\.]+"

        def replaceValueWithPlaceHolder(match: _tp.Match):
            return cls._processMatch(match, placeholder)

        actualContent = _re.sub(
            pattern, replaceValueWithPlaceHolder, actualContent, flags=_re.MULTILINE
        )

        return actualContent

    @staticmethod
    def _processMatch(match: _tp.Match, placeholder: str) -> str:
        matchedText = match[0]
        if matchedText == "MfrsupplyWater = 1000":
            return "MfrsupplyWater = 1000"

        variableName = match["variableName"]

        return f"{variableName} = {placeholder}"
