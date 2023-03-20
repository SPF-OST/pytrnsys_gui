import pytest as _pt

import trnsysGUI.connection.doublePipeConnectionModel as _dpcm

_JSON_VERSION_0 = {
    ".__ConnectionDict__": True,
    "__version__": "0810c9ea-85df-4431-bb40-3190c25c9161",
    "childIds": [2, 3, 4],
    "connectionId": 1,
    "fromPortId": 17,
    "id": 1,
    "labelPos": [1.1, 1.1],
    "massFlowLabelPos": [1.1, 0],
    "name": "dpc5",
    "segmentsCorners": [[0, 0], [0, 1], [1, 0], [1, 1]],
    "toPortId": 18,
    "trnsysId": 500,
}

_JSON_VERSION_1 = {
    ".__ConnectionDict__": True,
    "__version__": "bdb5f03b-75bb-4c2f-a658-0de489c5b017",
    "childIds": [2, 3, 4],
    "connectionId": 1,
    "fromPortId": 17,
    "id": 1,
    "labelPos": [1.1, 1.1],
    "lengthInM": 2.0,
    "massFlowLabelPos": [1.1, 0],
    "name": "dpc5",
    "segmentsCorners": [[0, 0], [0, 1], [1, 0], [1, 1]],
    "toPortId": 18,
    "trnsysId": 500,
}

_UPGRADED_MODEL = _dpcm.DoublePipeConnectionModel(
    connectionId=1,
    name="dpc5",
    id=1,
    childIds=[2, 3, 4],
    segmentsCorners=[(0, 0), (0, 1), (1, 0), (1, 1)],
    labelPos=(1.1, 1.1),
    massFlowLabelPos=(1.1, 0),
    fromPortId=17,
    toPortId=18,
    trnsysId=500,
    lengthInM=579.404,
)

_DESERIALIZED_MODEL = _dpcm.DoublePipeConnectionModel(
    connectionId=1,
    name="dpc5",
    id=1,
    childIds=[2, 3, 4],
    segmentsCorners=[(0, 0), (0, 1), (1, 0), (1, 1)],
    labelPos=(1.1, 1.1),
    massFlowLabelPos=(1.1, 0),
    fromPortId=17,
    toPortId=18,
    trnsysId=500,
    lengthInM=2.0,
)


_TO_DICT_CASES = [
    (_DESERIALIZED_MODEL, _JSON_VERSION_1),
]

_FROM_DICT_CASES = [
    (_dpcm.DoublePipeConnectionModel, _UPGRADED_MODEL, _JSON_VERSION_0),
    (_dpcm.DoublePipeConnectionModel, _DESERIALIZED_MODEL, _JSON_VERSION_1),
]


class TestDoublePipeConnectionModel:
    @_pt.mark.parametrize("model, json", _TO_DICT_CASES)
    def testToDict(self, model, json):
        data = model.to_dict()
        assert data == json

    @_pt.mark.parametrize("modelClass, model, json", _FROM_DICT_CASES)
    def testFromDict(self, modelClass, model, json):
        deserializedModel = modelClass.from_dict(json)
        assert deserializedModel == model

    def testGetSupersededClass(self):
        assert _dpcm.DoublePipeConnectionModel.getSupersededClass() == _dpcm.DoublePipeConnectionModelVersion0

    def testUpgrade(self):
        version0 = _dpcm.DoublePipeConnectionModelVersion0.from_dict(_JSON_VERSION_0)
        assert _dpcm.DoublePipeConnectionModel.upgrade(version0) == _UPGRADED_MODEL
