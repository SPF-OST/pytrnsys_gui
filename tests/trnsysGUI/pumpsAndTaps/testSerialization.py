import json as _json
import pathlib as _pl

import trnsysGUI.pumpsAndTaps._serialization as _ser


class TestSerialization:
    def testPumpModelVersion1RoundTrip(self):
        dataDirPath = _pl.Path(__file__).parent / "data"
        serializedModelVersion1FilePath = dataDirPath / "pumpModelVersion1.json"
        expectedSerializedModelFilePath = dataDirPath / "expectedPumpModel.json"

        with serializedModelVersion1FilePath.open(mode="tr", encoding="UTF8") as file:
            serializedModelVersion1 = _json.load(file)

        model = _ser.PumpModel.from_dict(serializedModelVersion1)
        serializedModelAsDict = model.to_dict()
        actualSerializedModel = _json.dumps(serializedModelAsDict, indent=2)

        expectedSerializedModel = expectedSerializedModelFilePath.read_text(encoding="UTF8")

        assert actualSerializedModel == expectedSerializedModel
