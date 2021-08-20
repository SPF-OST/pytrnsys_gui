import pathlib as _pl

import trnsysGUI.storageTank.model as _stm


class TestModel:
    def testConvertFromOldestToNewestFormat(self):  # pylint: disable=no-self-use
        expectedPath = (
            _pl.Path(__file__).parent.parent
            / "data"
            / "storageTankConvertedFromOldestToNewestBeforeSettingInvalidIDs.json"
        )
        expectedStorageTankJson = expectedPath.read_text()

        storageTankLegacyJsonPath = _pl.Path(__file__).parent.parent / "data" / "storageTankOldestFormat.json"
        storageTank = _stm.StorageTank.from_json(storageTankLegacyJsonPath.read_text())
        actualStorageTankJson = storageTank.to_json(indent=4, sort_keys=True)

        assert actualStorageTankJson == expectedStorageTankJson

    def testRoundTripWithNewestFormat(self):  # pylint: disable=no-self-use
        newestFormatPath = _pl.Path(__file__).parent.parent / "data" / "storageTankNewestFormat.json"
        newestFormatJson = newestFormatPath.read_text()

        storageTank = _stm.StorageTank.from_json(newestFormatJson)
        actualJson = storageTank.to_json(indent=4, sort_keys=True)

        assert actualJson == newestFormatJson
