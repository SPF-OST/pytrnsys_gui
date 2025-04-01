import collections.abc as _cabc
import pathlib as _pl

import pandas as _pd


def getRegimesFromFile(fileName: _pl.Path) -> _pd.DataFrame:
    table = _pd.read_csv(fileName)
    colName = "regimeName"
    if colName in table.keys():
        return table
    raise ValueError(f"Column name '{colName}' not found.")


def getRegimes(
    filePath: _pl.Path, onlyTheseRegimes: _cabc.Sequence[str] | None
) -> _pd.DataFrame:
    regimeValues = getRegimesFromFile(filePath)
    regimeValues = regimeValues.set_index("regimeName")
    if onlyTheseRegimes:
        return regimeValues.loc[onlyTheseRegimes]
    return regimeValues
