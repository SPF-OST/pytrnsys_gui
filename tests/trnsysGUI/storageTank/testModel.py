import pathlib as _pl

import trnsysGUI.storageTank.model as _stm


class TestModel:
    def testRoundTrip(self):  # pylint: disable=no-self-use
        expectedPath = _pl.Path(__file__).parent.parent / "data" / "storageTankConvertedToNewFormat.json"
        expectedStorageTankJson = expectedPath.read_text()

        storageTankLegacyJsonPath = _pl.Path(__file__).parent.parent / "data" / "storageTankLegacyFormat.json"
        storageTank\
            = _stm.StorageTank.from_json(storageTankLegacyJsonPath.read_text())
        actualStorageTankJson = storageTank.to_json(indent=4, sort_keys=True)

        assert actualStorageTankJson == expectedStorageTankJson
