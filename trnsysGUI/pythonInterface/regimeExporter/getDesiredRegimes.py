import pandas as _pd

# dealing with files where the regimeName column is not provided correctly


def getRegimesFromFile(fileName):
    df = _pd.read_csv(fileName)
    _COL_NAME_ = "regimeName"
    if _COL_NAME_ in df.keys():
        return df
    raise ValueError(f"Column name '{_COL_NAME_}' not found.")

# error handling?
#   - will throw "fileNotFoundError" as it is.
#
#
# regimeName, name1, name2, name3
# regime, value1, value2, value3
#
# if isPump(name):
# if isValve(name):