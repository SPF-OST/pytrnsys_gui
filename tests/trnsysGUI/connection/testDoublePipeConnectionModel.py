import dataclasses as _dc

import dataclasses_jsonschema as _dcj
import pytest as _pt

import pytrnsys.utils.serialization as _ser
import trnsysGUI.connection.doublePipeConnectionModel as _dpcm


@_dc.dataclass
class _DeserializationTestCase:
    json: _dcj.JsonDict
    model: _ser.UpgradableJsonSchemaMixinVersion0
    needsUpgrading: bool = False

    def name(self) -> str:
        className = type(self.model).__name__
        upgrading = "upgrading" if self.needsUpgrading else "not-upgrading"
        return f"{className}/{upgrading}"


@_dc.dataclass
class _SuperseedsTestCase:
    previousVersionModel: _ser.UpgradableJsonSchemaMixinVersion0
    currentVersionModel: _ser.UpgradableJsonSchemaMixin

    def name(self) -> str:
        previousClazzName = type(self.previousVersionModel).__name__
        currentClazzName = type(self.currentVersionModel).__name__
        return f"{previousClazzName}->{currentClazzName}"


_JSON_VERSION_0 = {
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

_JSON_VERSION_1 = _JSON_VERSION_0.copy()
_JSON_VERSION_1["__version__"] = "bdb5f03b-75bb-4c2f-a658-0de489c5b017"
_JSON_VERSION_1["lengthInM"] = 2.0

_JSON_VERSION_1_FOR_UPGRADING = _JSON_VERSION_1.copy()
_JSON_VERSION_1_FOR_UPGRADING[".__ConnectionDict__"] = True

_JSON_VERSION_2 = _JSON_VERSION_1.copy()
_JSON_VERSION_2[".__ConnectionDict__"] = True
_JSON_VERSION_2["__version__"] = "62a1383d-5a0b-4886-9951-31ffd732637d"
_JSON_VERSION_2["shallBeSimulated"] = False


_DESERIALIZED_MODEL_VERSION_0 = _dpcm.DoublePipeConnectionModelVersion0(
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
)

_UPGRADED_MODEL_VERSION_1 = _dpcm.DoublePipeConnectionModelVersion1(
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

_DESERIALIZED_MODEL_VERSION_1 = _dpcm.DoublePipeConnectionModelVersion1(
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
    lengthInM=2.0,
    shallBeSimulated=True,
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
    shallBeSimulated=False,
)


_SERIALIZATION_CASES = [
    (_DESERIALIZED_MODEL, _JSON_VERSION_2),
]


_DESERIALIZATION_TEST_CASES = [
    _DeserializationTestCase(_JSON_VERSION_0, _DESERIALIZED_MODEL_VERSION_0),
    _DeserializationTestCase(_JSON_VERSION_0, _UPGRADED_MODEL_VERSION_1, needsUpgrading=True),
    _DeserializationTestCase(_JSON_VERSION_1, _DESERIALIZED_MODEL_VERSION_1),
    _DeserializationTestCase(_JSON_VERSION_1_FOR_UPGRADING, _UPGRADED_MODEL, needsUpgrading=True),
    _DeserializationTestCase(_JSON_VERSION_2, _DESERIALIZED_MODEL),
]


_SUPERSEEDS_TEST_CASES = [
    _SuperseedsTestCase(_DESERIALIZED_MODEL_VERSION_0, _UPGRADED_MODEL_VERSION_1),
    _SuperseedsTestCase(_DESERIALIZED_MODEL_VERSION_1, _UPGRADED_MODEL),
]


class TestDoublePipeConnectionModel:
    @_pt.mark.parametrize("model, json", _SERIALIZATION_CASES)
    def testSerialize(self, model, json):
        data = model.to_dict()
        assert data == json

    @_pt.mark.parametrize("deserializationTestCase", _DESERIALIZATION_TEST_CASES, ids=_DeserializationTestCase.name)
    def testDeserialize(self, deserializationTestCase: _DeserializationTestCase):
        clazz = type(deserializationTestCase.model)
        deserializedModel = clazz.from_dict(deserializationTestCase.json)
        assert deserializedModel == deserializationTestCase.model

    @_pt.mark.parametrize("superseedsTestCase", _SUPERSEEDS_TEST_CASES, ids=_SuperseedsTestCase.name)
    def testGetSupersededClass(self, superseedsTestCase: _SuperseedsTestCase):
        superseedingClass = type(superseedsTestCase.currentVersionModel)
        superseededClass = type(superseedsTestCase.previousVersionModel)
        assert superseedingClass.getSupersededClass() == superseededClass

    @_pt.mark.parametrize("superseedsTestCase", _SUPERSEEDS_TEST_CASES, ids=_SuperseedsTestCase.name)
    def testUpgrade(self, superseedsTestCase: _SuperseedsTestCase):
        superseedingClass = type(superseedsTestCase.currentVersionModel)

        upgradedModel = superseedingClass.upgrade(superseedsTestCase.previousVersionModel)
        assert upgradedModel == superseedsTestCase.currentVersionModel
