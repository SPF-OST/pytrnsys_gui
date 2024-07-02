import json

import pandas as _pd

import trnsysGUI.pumpsAndTaps.serialization as _se


def exportRegimeTemplate(projectJson, regimeFileName):
    pumpsAndValvesAndValues = getPumpsAndValvesWithValuesFromJson(projectJson)
    writeToCsv(pumpsAndValvesAndValues, regimeFileName)


def getPumpsAndValvesWithValuesFromJson(projectJson):
    with open(projectJson, "r", encoding="utf-8") as openFile:
        jsonValues = json.load(openFile)

    data = {}
    undesiredBlocks = [".__BlockDct__", "IDs", "Strings"]
    for block in jsonValues["Blocks"]:
        if block in undesiredBlocks:
            continue

        curDict = jsonValues["Blocks"][block]
        if "BlockName" in curDict:
            curBlockName = curDict["BlockName"]
            if curBlockName == "Pump":
                curPump = _se.PumpModel.from_dict(curDict)
                data[curPump.BlockDisplayName] = curPump.blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

            elif curBlockName == "TVentil":
                desiredValueName = "PositionForMassFlowSolver"
                data = getData(curDict, data, desiredValueName)

            elif curBlockName in ("WTap_main", "WTap"):
                curTap = _se.TerminalWithPrescribedMassFlowModel.from_dict(curDict)
                data[curTap.BlockDisplayName] = curTap.blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

    pumpsAndValvesAndValues = _pd.DataFrame(data, index=["dummy_regime"])
    pumpsAndValvesAndValues.index.name = "regimeName"
    return pumpsAndValvesAndValues


def getData(curDict, data, desiredValueName):
    blockItemName = curDict["BlockDisplayName"]
    value = float(curDict[desiredValueName])
    data[blockItemName] = value
    return data


def writeToCsv(pumpsAndValvesAndValues, regimeFileName):
    pumpsAndValvesAndValues = pumpsAndValvesAndValues.sort_index(axis="columns")
    pumpsAndValvesAndValues.to_csv(regimeFileName)
