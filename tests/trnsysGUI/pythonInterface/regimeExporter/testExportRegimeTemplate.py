import pathlib as _pl
import pandas as _pd

import trnsysGUI as _GUI
import trnsysGUI.pythonInterface.regimeExporter.exportRegimes as _er

_PROJECT_NAME = "diagramForRegimes"
_DATA_DIR = _pl.Path(_GUI.__file__).parent / f"..\\tests\\trnsysGUI\\data\\{_PROJECT_NAME}"
_EXPECTED_CVSS_DIR = _DATA_DIR / "expectedCSVs"


class TestExportRegimeTemplate:
    def testExportTemplate(self):
        projectJson = _DATA_DIR / f"{_PROJECT_NAME}.json"
        regimeFileName = _DATA_DIR / "regimeTemplate.csv"
        expectedFileName = _EXPECTED_CVSS_DIR / "expectedRegimeTemplate.csv"

        _er.exportRegimeTemplate(projectJson, regimeFileName)

        expectedContent = _pd.read_csv(expectedFileName)
        actualContent = _pd.read_csv(regimeFileName)

        _pd.testing.assert_frame_equal(expectedContent, actualContent, check_dtype=False)
