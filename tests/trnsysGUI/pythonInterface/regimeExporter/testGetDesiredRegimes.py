import pandas as _pd
import pathlib as _pl

import trnsysGUI.pythonInterface.regimeExporter.getDesiredRegimes as _gdr
import trnsysGUI as _GUI

_DATA_DIR_ = _pl.Path(_GUI.__file__).parent / "..\\tests\\trnsysGUI\\data"


class TestGetDesiredRegimes:
    def testgetRegimesFromFile(self):
        fileName = _DATA_DIR_ / "regimes.csv"
        df1 = _gdr.getRegimesFromFile(fileName)
        df2 = _pd.DataFrame(
            {
                "regimeNames": ["name1", "name2", "throws"],
                "pump1": [500, 500, 0],
                "pump2": [0, 500, 0],
                "pump3": [500, 0, 500],
                "valve1": [0, 0, 0],
                "valve2": [0, 1, 1],
            }
        )
        assert df1.equals(df2)
