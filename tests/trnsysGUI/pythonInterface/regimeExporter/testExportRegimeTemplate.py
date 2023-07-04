import pathlib as _pl

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

        expectedContent = _pl.Path(expectedFileName).read_text(encoding="utf-8")
        actualContent = _pl.Path(regimeFileName).read_text(encoding="utf-8")

        assert actualContent == expectedContent
