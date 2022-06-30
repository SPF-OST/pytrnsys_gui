import pathlib as _pl

import trnsysGUI.storageTank.model as _stm


class TestModel:
    DATA_DIR_PATH = _pl.Path(__file__).parent.parent / "data"
    EXPECTED_DIR_PATH = DATA_DIR_PATH / "expected"

    def testConvertFromOldestToNewestFormat(self):
        expectedPath = self.EXPECTED_DIR_PATH / "storageTankConvertedFromOldestToNewestBeforeSettingInvalidIDs.json"
        expectedStorageTankJson = expectedPath.read_text()

        storageTankLegacyJsonPath = self.DATA_DIR_PATH / "storageTankOldestFormat.json"
        storageTank = _stm.StorageTank.from_json(storageTankLegacyJsonPath.read_text())
        actualStorageTankJson = storageTank.to_json(indent=4, sort_keys=True)

        assert actualStorageTankJson == expectedStorageTankJson

    def testRoundTripWithNewestFormat(self):
        newestFormatPath = self.EXPECTED_DIR_PATH / "storageTankNewestFormat.json"
        newestFormatJson = newestFormatPath.read_text()

        storageTank = _stm.StorageTank.from_json(newestFormatJson)
        actualJson = storageTank.to_json(indent=4, sort_keys=True)

        assert actualJson == newestFormatJson
