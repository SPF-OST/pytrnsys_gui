import pathlib as _pl

import trnsysGUI as _GUI
import trnsysGUI.pythonInterface.regimeExporter.exportRegimes as _er

_PROJECT_NAME_ = "diagramForRegimes"
_DATA_DIR_ = _pl.Path(_GUI.__file__).parent / f"..\\tests\\trnsysGUI\\data\\{_PROJECT_NAME_}"
_EXPECTED_CVSS_DIR_ = _DATA_DIR_ / "expectedCSVs"


class TestExportRegimeTemplate:
    def testExportTemplate(self):
        projectJson = _DATA_DIR_ / f"{_PROJECT_NAME_}.json"
        regimeFileName = _DATA_DIR_ / "regimeTemplate.csv"
        expectedFileName = _EXPECTED_CVSS_DIR_ / "expectedRegimeTemplate.csv"

        _er.exportRegimeTemplate(projectJson, regimeFileName)

        expectedContent = _pl.Path(expectedFileName).read_text()
        actualContent = _pl.Path(regimeFileName).read_text()

        assert actualContent == expectedContent
