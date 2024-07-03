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
    blockItemsAndConnections = jsonValues["Blocks"].values()
    blockItems = [bc for bc in blockItemsAndConnections if isinstance(bc, dict) and ".__BlockDict__" in bc]

    pumps = [b for b in blockItems if b["BlockName"] == "Pump"]
    for pump in pumps:
        curBlockItem = _se.PumpModel.from_dict(pump)
        data[curBlockItem.BlockDisplayName] = curBlockItem.blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

    valves = [b for b in blockItems if b["BlockName"] == "TVentil"]
    for valve in valves:
        desiredValueName = "PositionForMassFlowSolver"
        data = getData(valve, data, desiredValueName)

    taps = [b for b in blockItems if b["BlockName"] in ("WTap_main", "WTap")]
    for tap in taps:
        curBlockItem = _se.TerminalWithPrescribedMassFlowModel.from_dict(tap)
        data[curBlockItem.BlockDisplayName] = curBlockItem.blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

    sourceSinks = [
        b for b in blockItems if b["BlockName"] in ("Sink", "Source", "SourceSink", "Geotherm", "Water")
    ]
    for sourceSink in sourceSinks:
        # This isn't in the json yet, so I am applying a default value directly at first.
        blockDisplayName = sourceSink["BlockDisplayName"]
        data[blockDisplayName] = 500.0

    componentsAndValues = _pd.DataFrame(data, index=["dummy_regime"])
    componentsAndValues.index.name = "regimeName"

    return componentsAndValues


def getData(curDict, data, desiredValueName):
    blockItemName = curDict["BlockDisplayName"]
    value = float(curDict[desiredValueName])
    data[blockItemName] = value
    return data


def writeToCsv(pumpsAndValvesAndValues, regimeFileName):
    pumpsAndValvesAndValues = pumpsAndValvesAndValues.sort_index(axis="columns")
    pumpsAndValvesAndValues.to_csv(regimeFileName)
