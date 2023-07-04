import json

import pandas as _pd


def exportRegimeTemplate(projectJson, regimeFileName):
    pumpsAndValvesAndValues = getPumpsAndValvesWithValuesFromJson(projectJson)
    writeToCsv(pumpsAndValvesAndValues, regimeFileName)


def getPumpsAndValvesWithValuesFromJson(projectJson):
    with open(projectJson, 'r', encoding='utf-8') as openFile:
        jsonValues = json.load(openFile)

    data = {}
    undesiredBlocks = [".__BlockDct__", "IDs", "Strings"]
    for block in jsonValues["Blocks"]:
        if block not in undesiredBlocks:
            curDict = jsonValues["Blocks"][block]
            if "BlockName" in curDict:
                curBlockName = curDict["BlockName"]
                if curBlockName == "Pump":
                    desiredValueName = "massFlowRateInKgPerH"
                    data = getData(curDict, data, desiredValueName)
                elif curBlockName == "TVentil":
                    desiredValueName = "PositionForMassFlowSolver"
                    data = getData(curDict, data, desiredValueName)
    pumpsAndValvesAndValues = _pd.DataFrame(data, index=["'dummy regime'"])
    pumpsAndValvesAndValues.index.name = "regimeName"
    return pumpsAndValvesAndValues


def getData(curDict, data, desiredValueName):
    label = curDict["BlockDisplayName"]
    value = float(curDict[desiredValueName])
    data[label] = value
    return data


def writeToCsv(pumpsAndValvesAndValues, regimeFileName):
    pumpsAndValvesAndValues = pumpsAndValvesAndValues.sort_index(axis="columns")
    pumpsAndValvesAndValues.to_csv(regimeFileName)
