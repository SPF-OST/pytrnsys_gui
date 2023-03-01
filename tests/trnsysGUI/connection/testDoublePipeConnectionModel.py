import uuid as _uuid
import pytest as _pt

import trnsysGUI.connection.doublePipeConnectionModel as _dpcm

_JSON_VERSION_0 = {'__version__': '0810c9ea-85df-4431-bb40-3190c25c9161',
                   'childIds': [2, 3, 4],
                   'connectionId': 1,
                   'fromPortId': 17,
                   'id': 1,
                   'labelPos': [1.1, 1.1],
                   'massFlowLabelPos': [1.1, 0],
                   'name': 'dpc5',
                   'segmentsCorners': [[0, 0], [0, 1], [1, 0], [1, 1]],
                   'toPortId': 18,
                   'trnsysId': 500}

_JSON_VERSION_0_FROM = {'.__ConnectionDict__': True,
                        '__version__': '0810c9ea-85df-4431-bb40-3190c25c9161',
                        'childIds': [2, 3, 4],
                        'connectionId': 1,
                        'fromPortId': 17,
                        'id': 1,
                        'labelPos': [1.1, 1.1],
                        'massFlowLabelPos': [1.1, 0],
                        'name': 'dpc5',
                        'segmentsCorners': [[0, 0], [0, 1], [1, 0], [1, 1]],
                        'toPortId': 18,
                        'trnsysId': 500}

_JSON_VERSION_1 = {'.__ConnectionDict__': True,
                   '__version__': 'bdb5f03b-75bb-4c2f-a658-0de489c5b017',
                   'childIds': [2, 3, 4],
                   'connectionId': 1,
                   'fromPortId': 17,
                   'id': 1,
                   'labelPos': [1.1, 1.1],
                   'lengthInM': 2.0,
                   'massFlowLabelPos': [1.1, 0],
                   'name': 'dpc5',
                   'segmentsCorners': [[0, 0], [0, 1], [1, 0], [1, 1]],
                   'toPortId': 18,
                   'trnsysId': 500}

_TO_DICT_CASES = [
    ("model0", _JSON_VERSION_0),
    ("model1", _JSON_VERSION_1),
]

_FROM_DICT_CASES = [
    ("DoublePipeConnectionModelVersion0", "model0", _JSON_VERSION_0_FROM),
    ("DoublePipeConnectionModel", "model1", _JSON_VERSION_1),
]

_VERSION_CASES = [(x, z) for x, y, z in _FROM_DICT_CASES]


class TestDoublePipeConnectionModel:
    def setup(self):
        self.model0 = _dpcm.DoublePipeConnectionModelVersion0(  # pylint: disable=attribute-defined-outside-init
            connectionId=1,
            name="dpc5",
            id=1,
            childIds=[2, 3, 4],
            segmentsCorners=[(0, 0), (0, 1), (1, 0), (1, 1)],
            labelPos=(1.1, 1.1),
            massFlowLabelPos=(1.1, 0),
            fromPortId=17,
            toPortId=18,
            trnsysId=500
        )
        self.model1 = _dpcm.DoublePipeConnectionModel(connectionId=1,  # pylint: disable=attribute-defined-outside-init
                                                      name="dpc5",
                                                      id=1,
                                                      childIds=[2, 3, 4],
                                                      segmentsCorners=[(0, 0), (0, 1), (1, 0), (1, 1)],
                                                      labelPos=(1.1, 1.1),
                                                      massFlowLabelPos=(1.1, 0),
                                                      fromPortId=17,
                                                      toPortId=18,
                                                      trnsysId=500,
                                                      lengthInM=2.0
                                                      )

    @_pt.mark.parametrize("model, json", _TO_DICT_CASES)
    def testToDict(self, model, json):
        data = getattr(self, model).to_dict()
        assert data == json

    @_pt.mark.parametrize("modelVersion, model, json", _FROM_DICT_CASES)
    def testFromDict(self, modelVersion, model, json):
        result = getattr(_dpcm, modelVersion).from_dict(json)
        assert result == getattr(self, model)

    @_pt.mark.parametrize("modelVersion, json", _VERSION_CASES)
    def testGetVersion(self, modelVersion, json):
        version = getattr(_dpcm, modelVersion).getVersion()
        assert version == _uuid.UUID(json['__version__'])

    def testGetSupersededClass(self):
        assert _dpcm.DoublePipeConnectionModel.getSupersededClass() == _dpcm.DoublePipeConnectionModelVersion0

    def testUpgrade(self):
        assert _dpcm.DoublePipeConnectionModel.upgrade(self.model0) == self.model1
