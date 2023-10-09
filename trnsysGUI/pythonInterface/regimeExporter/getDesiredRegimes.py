import pandas as _pd

# dealing with files where the regimeName column is not provided correctly


def getRegimesFromFile(fileName):
    table = _pd.read_csv(fileName)
    colName = "regimeName"
    if colName in table.keys():
        return table
    raise ValueError(f"Column name '{colName}' not found.")


# error handling?
#   - will throw "fileNotFoundError" as it is.
#
#
# regimeName, name1, name2, name3
# regime, value1, value2, value3
#
# if isPump(name):
# if isValve(name):


def getRegimes(filePath, onlyTheseRegimes):
    regimeValues = getRegimesFromFile(filePath)
    regimeValues = regimeValues.set_index("regimeName")
    if onlyTheseRegimes:
        return regimeValues.loc[onlyTheseRegimes]
    return regimeValues
