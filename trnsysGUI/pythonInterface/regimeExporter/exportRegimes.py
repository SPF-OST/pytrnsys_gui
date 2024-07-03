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
    blocks = jsonValues["Blocks"]
    undesiredBlocks = [".__BlockDct__", "IDs", "Strings"]
    # blockItemsInJson = filter(lambda x: x not in undesiredBlocks, blocks)
    # blockNamesInJson = list(filter(lambda block: "BlockName" in blocks[block], blockItemsInJson))
    blockItemsInJson = [x for x in blocks if x not in undesiredBlocks]
    blockNamesInJson = [x for x in blockItemsInJson if "BlockName" in blocks[x]]

    # pumps = list(filter(lambda block: "Pump" in blocks[block]["BlockName"], blockNamesInJson))
    pumps = [x for x in blockNamesInJson if blocks[x]["BlockName"] == "Pump"]
    for pump in pumps:
        curPump = _se.PumpModel.from_dict(blocks[pump])
        data[curPump.BlockDisplayName] = curPump.blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

    # valves = list(filter(lambda block: "TVentil" in blocks[block]["BlockName"], blockNamesInJson))
    valves = [x for x in blockNamesInJson if blocks[x]["BlockName"] == "TVentil"]
    for valve in valves:
        desiredValueName = "PositionForMassFlowSolver"
        data = getData(blocks[valve], data, desiredValueName)

    # taps = list(filter(lambda block: blocks[block]["BlockName"] in ("WTap_main", "WTap"), blockNamesInJson))
    taps = [x for x in blockNamesInJson if blocks[x]["BlockName"] in ("WTap_main", "WTap")]
    for tap in taps:
        curTap = _se.TerminalWithPrescribedMassFlowModel.from_dict(blocks[tap])
        data[curTap.BlockDisplayName] = curTap.blockItemWithPrescribedMassFlow.massFlowRateInKgPerH

    sourceSinks = [x for x in blockNamesInJson if blocks[x]["BlockName"] in ("Sink", "Source", "SourceSink", "Geotherm", "Water")]
    for sourceSink in sourceSinks:
        """ This isn't in the json yet, so I am applying a default value directly at first. """
        BlockDisplayName = blocks[sourceSink]["BlockDisplayName"]
        data[BlockDisplayName] = 500.0

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
