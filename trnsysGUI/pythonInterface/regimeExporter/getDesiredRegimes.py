import pandas as _pd


def getRegimesFromFile(fileName):
    table = _pd.read_csv(fileName)
    colName = "regimeName"
    if colName in table.keys():
        return table
    raise ValueError(f"Column name '{colName}' not found.")


def getRegimes(filePath, onlyTheseRegimes):
    regimeValues = getRegimesFromFile(filePath)
    regimeValues = regimeValues.set_index("regimeName")
    if onlyTheseRegimes:
        return regimeValues.loc[onlyTheseRegimes]
    return regimeValues
