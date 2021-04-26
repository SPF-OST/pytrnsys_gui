import copy as _cp
import dataclasses as _dc
import json as _json

import pytest as _pt

import trnsysGUI.serialization as _ser


@_dc.dataclass
class PersonVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    firstName: str
    age: int
    heightInM: float


@_dc.dataclass
class PersonVersion1(_ser.UpgradableJsonSchemaMixin, supersedes=PersonVersion0):
    firstName: str
    lastName: str
    age: int
    heightInCm: int

    @classmethod
    def _fromSuperseded(cls, superseded: PersonVersion0) -> "PersonVersion1":
        lastName = ""
        heightInCm = round(superseded.heightInM * 100)
        return PersonVersion1(
            superseded.firstName, lastName, superseded.age, heightInCm
        )


@_dc.dataclass
class Person(_ser.UpgradableJsonSchemaMixin, supersedes=PersonVersion1):
    title: str
    lastName: str
    ageInYears: int
    heightInCm: int

    @classmethod
    def _fromSuperseded(cls, superseded: PersonVersion1) -> "Person":
        title = ""
        ageInYears = superseded.age
        return Person(title, superseded.lastName, ageInYears, superseded.heightInCm)


class TestSerialization:
    SERIALIZED_P0 = {"firstName": "Damian", "age": 32, "heightInM": 1.73, "_VERSION": 0}
    SERIALIZED_P1 = {
        "_VERSION": 1,
        "age": 32,
        "firstName": "Damian",
        "heightInCm": 173,
        "lastName": "Birchler",
    }
    SERIALIZED_P = {
        "_VERSION": 2,
        "ageInYears": 32,
        "heightInCm": 173,
        "lastName": "Birchler",
        "title": "Mr.",
    }

    def testSerialization(self):
        p0 = PersonVersion0(firstName="Damian", age=32, heightInM=1.73)
        assert p0.to_dict() == self.SERIALIZED_P0

        p1 = PersonVersion1(
            firstName="Damian", lastName="Birchler", age=32, heightInCm=173
        )
        assert p1.to_dict() == self.SERIALIZED_P1

        p = Person(title="Mr.", lastName="Birchler", ageInYears=32, heightInCm=173)
        assert p.to_dict() == self.SERIALIZED_P

    def testStandardUseCase(self):
        json = _json.dumps(self.SERIALIZED_P0)

        p = Person.fromUpgradableJson(json)

        assert p._VERSION is 2
        assert p.title is ""
        assert p.lastName is ""
        assert p.ageInYears == self.SERIALIZED_P0["age"]
        assert p.heightInCm == self.SERIALIZED_P0["heightInM"] * 100

    def testWrongVersionRaises(self):
        serializedP1 = _cp.deepcopy(self.SERIALIZED_P1)
        serializedP1["_VERSION"] = 4
        json = _json.dumps(serializedP1)

        with _pt.raises(ValueError):
            Person.fromUpgradableJson(json)

    def testMissingVersion0DoesNotRaise(self):
        serializedP0 = _cp.deepcopy(self.SERIALIZED_P0)
        del serializedP0["_VERSION"]

        json = _json.dumps(serializedP0)

        Person.fromUpgradableJson(json)

    def testMissingVersionRaises(self):
        serializedP = _cp.deepcopy(self.SERIALIZED_P)
        del serializedP["_VERSION"]

        json = _json.dumps(serializedP)

        with _pt.raises(ValueError):
            Person.fromUpgradableJson(json)
