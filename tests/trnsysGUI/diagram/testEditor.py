# pylint: skip-file
# type: ignore

import logging as log
import pathlib as pl
import shutil as sh
import re

import PyQt5.QtWidgets as widgets

import trnsysGUI.diagram.Editor as de


class TestEditor:
    def testExportForMassFlowSolver(self):
        helper = _Helper()
        helper.setup()

        # The following line is required otherwise QT will crash
        _ = widgets.QApplication([])

        logger = log.Logger("root")
        editor = de.Editor(
            parent=None, projectFolder=str(helper.projectFolderPath), jsonPath=None, loadValue="load", logger=logger
        )
        editor.exportData(exportTo="mfs")

        helper.ensureDckFilesAreEqualIgnoringRandomizedFlowRateValues()


class _Helper:
    RANDOMIZED_FLOW_RATES = "MfrPuSH MfrPuHpEvap MfrPuHpShCond MfrPuHpDhwCond MfrPuDhw MfrPuCirc".split()

    def __init__(self):
        dataFolderPath = pl.Path(__file__).parent / "data"

        self._actualFolderPath = dataFolderPath / "actual"

        self.projectFolderPath = self._actualFolderPath / "TRIHP_dualSource"
        expectedProjectFolderPath = dataFolderPath / "expected" / "TRIHP_dualSource"

        self._actualDckFile = self.projectFolderPath / "TRIHP_dualSource_mfs.dck"
        self._expectedDckFile = expectedProjectFolderPath / "TRIHP_dualSource_mfs.dck"

    def setup(self):
        self._copyExampleToTestInputFolder()

    def ensureDckFilesAreEqualIgnoringRandomizedFlowRateValues(self):
        actualContent = self._actualDckFile.read_text()
        expectedContent = self._expectedDckFile.read_text()

        actualContentWithoutRandomizedValues = self._replaceRandomizeValuesWithPlaceholder(
            actualContent, placeholder="XXX"
        )

        assert actualContentWithoutRandomizedValues == expectedContent

    def _copyExampleToTestInputFolder(self):
        if self._actualFolderPath.exists():
            sh.rmtree(self._actualFolderPath)

        pytrnsysGuiDir = pl.Path(__file__).parents[3]
        exampleFolderPath = pytrnsysGuiDir / "data" / "examples" / "TRIHP_dualSource"

        sh.copytree(exampleFolderPath, self.projectFolderPath)

    def _replaceRandomizeValuesWithPlaceholder(self, actualContent, placeholder):
        for massFlow in self.RANDOMIZED_FLOW_RATES:
            pattern = rf"^{massFlow} = [0-9\.]+"
            actualContent = re.sub(pattern, f"{massFlow} = {placeholder}", actualContent, flags=re.MULTILINE)

        return actualContent
