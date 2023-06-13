import pandas as _pd


def getRegimesFromFile(fileName):
    df = _pd.read_csv(fileName)
    return df


#
#
# regimeName, name1, name2, name3
# regime, value1, value2, value3
#
# if isPump(name):
# if isValve(name):