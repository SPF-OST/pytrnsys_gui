import pathlib as _pl
import pandas as _pd
import pytest as _pt

import trnsysGUI as _GUI
import trnsysGUI.pythonInterface.regimeExporter.exportRegimes as _er

_DATA_DIR_BASE = _pl.Path(_GUI.__file__).parent / "..\\tests\\trnsysGUI\\data\\"


class TestExportRegimeTemplate:

    @_pt.mark.parametrize(
        "projectName", ["diagramForRegimes", "diagramWithTapForRegimes", "diagramWithSourceSinksForRegimes"]
    )
    def testExportTemplate(self, projectName):
        dataDir = _DATA_DIR_BASE / f"{projectName}"
        expectedCsvDir = dataDir / "expectedCSVs"
        projectJson = dataDir / f"{projectName}.json"
        regimeFilePath = dataDir / "regimeTemplate.csv"
        expectedFilePath = expectedCsvDir / "expectedRegimeTemplate.csv"

        _er.exportRegimeTemplate(projectJson, regimeFilePath)

        expectedContent = _pd.read_csv(expectedFilePath)
        actualContent = _pd.read_csv(regimeFilePath)

        _pd.testing.assert_frame_equal(expectedContent, actualContent, check_dtype=False)
