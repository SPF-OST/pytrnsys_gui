import trnsysGUI.storage_tank.model as _stm


class TestModel:
    def testRoundTrip(self):
        storageTankLegacyJson = """{
    ".__BlockDict__": true,
    "BlockDisplayName": "Dhw",
    "BlockName": "StorageTank",
    "FlippedH": false,
    "FlippedV": false,
    "GroupName": "defaultGroup",
    "HxList": [
        {
            "DisplayName": "SolarHx",
            "Height": 40.0,
            "ID": 1976,
            "Offset": [
                0.0,
                154.0
            ],
            "ParentID": 1975,
            "Port1ID": 1977,
            "Port2ID": 1978,
            "SideNr": 0,
            "Width": 40,
            "connTrnsysID": 639
        }
    ],
    "ID": 1975,
    "PortPairList": [
        {
            "ConnCID": 440,
            "ConnDisName": "TesDHWPortHpDhw",
            "ConnID": 1984,
            "Port1ID": 1982,
            "Port1offset": 11.0,
            "Port2ID": 1983,
            "Port2offset": 142.0,
            "Side": true,
            "trnsysID": 641
        },
        {
            "ConnCID": 881,
            "ConnDisName": "TesDHWPortDhwRecir",
            "ConnID": 3926,
            "Port1ID": 3924,
            "Port1offset": 66.0,
            "Port2ID": 3925,
            "Port2offset": 22.0,
            "Side": false,
            "trnsysID": 1271
        },
        {
            "ConnCID": 886,
            "ConnDisName": "TesDHWPortDHW",
            "ConnID": 3943,
            "Port1ID": 3941,
            "Port1offset": 209.0,
            "Port2ID": 3942,
            "Port2offset": 11.0,
            "Side": false,
            "trnsysID": 1277
        }
    ],
    "StoragePosition": [
        -681.9155092592591,
        -581.1302806712963
    ],
    "size_h": 220.0,
    "trnsysID": 638
}"""
        expectedStorageTankJson = """{
    ".__BlockDict__": true,
    "BlockDisplayName": "Dhw",
    "BlockName": "StorageTank",
    "__version__": "05f422d3-41fd-48d1-b8d0-4655d9f65247",
    "directPortPairs": [
        {
            "connectionId": 440,
            "id": 1984,
            "portPair": {
                "inputPort": {
                    "id": 1982,
                    "relativeHeight": 0.95
                },
                "name": "TesDHWPortHpDhw",
                "outputPort": {
                    "id": 1983,
                    "relativeHeight": 0.35
                },
                "side": "left"
            },
            "trnsysId": 641
        },
        {
            "connectionId": 881,
            "id": 3926,
            "portPair": {
                "inputPort": {
                    "id": 3924,
                    "relativeHeight": 0.7
                },
                "name": "TesDHWPortDhwRecir",
                "outputPort": {
                    "id": 3925,
                    "relativeHeight": 0.9
                },
                "side": "right"
            },
            "trnsysId": 1271
        },
        {
            "connectionId": 886,
            "id": 3943,
            "portPair": {
                "inputPort": {
                    "id": 3941,
                    "relativeHeight": 0.05
                },
                "name": "TesDHWPortDHW",
                "outputPort": {
                    "id": 3942,
                    "relativeHeight": 0.95
                },
                "side": "right"
            },
            "trnsysId": 1277
        }
    ],
    "groupName": "defaultGroup",
    "heatExchangers": [
        {
            "connectionTrnsysId": 639,
            "id": 1976,
            "parentId": 1975,
            "portPair": {
                "inputPort": {
                    "id": 1977,
                    "relativeHeight": 0.3
                },
                "name": "SolarHx",
                "outputPort": {
                    "id": 1978,
                    "relativeHeight": 0.12
                },
                "side": "left"
            },
            "width": 40
        }
    ],
    "height": 220.0,
    "id": 1975,
    "isHorizontallyFlipped": false,
    "isVerticallyFlipped": false,
    "position": [
        -681.9155092592591,
        -581.1302806712963
    ],
    "trnsysId": 638
}"""
        storageTank\
            = _stm.StorageTank.from_json(storageTankLegacyJson)
        actualStorageTankJson = storageTank.to_json(indent=4, sort_keys=True)

        assert actualStorageTankJson == expectedStorageTankJson

