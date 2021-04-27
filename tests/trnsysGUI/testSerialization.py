import copy as _cp
import dataclasses as _dc
import json as _json
import uuid as _uuid
import typing as _tp

import pytest as _pt

import trnsysGUI.serialization as _ser


@_dc.dataclass
class PersonVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    firstName: str
    age: int
    heightInM: float

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("ff2ba3c8-4fef-4a64-a026-11212ab35d6b")


@_dc.dataclass
class PersonVersion1(_ser.UpgradableJsonSchemaMixin):
    firstName: str

    lastName: str
    age: int
    heightInCm: int

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[PersonVersion0]:
        return PersonVersion0

    @classmethod
    def fromSuperseded(cls, superseded: PersonVersion0) -> "PersonVersion1":
        lastName = ""
        heightInCm = round(superseded.heightInM * 100)
        return PersonVersion1(
            superseded.firstName, lastName, superseded.age, heightInCm
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("70d5694f-032c-4ca8-b13c-c020b05f2179")


@_dc.dataclass
class Person(_ser.UpgradableJsonSchemaMixin):
    title: str
    lastName: str
    ageInYears: int
    heightInCm: int

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[PersonVersion1]:
        return PersonVersion1

    @classmethod
    def fromSuperseded(cls, superseded: PersonVersion1) -> "Person":
        title = ""
        ageInYears = superseded.age
        return Person(title, superseded.lastName, ageInYears, superseded.heightInCm)

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("1774d088-3917-4c29-a76a-0a4514ef6cf5")


class TestSerialization:
    SERIALIZED_P0 = {
        "__version__": "ff2ba3c8-4fef-4a64-a026-11212ab35d6b",
        "age": 32,
        "firstName": "Damian",
        "heightInM": 1.73,
    }
    SERIALIZED_P1 = {
        "__version__": "70d5694f-032c-4ca8-b13c-c020b05f2179",
        "age": 32,
        "firstName": "Damian",
        "heightInCm": 173,
        "lastName": "Birchler",
    }
    SERIALIZED_P = {
        "__version__": "1774d088-3917-4c29-a76a-0a4514ef6cf5",
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

        assert p.title is ""
        assert p.lastName is ""
        assert p.ageInYears == self.SERIALIZED_P0["age"]
        assert p.heightInCm == self.SERIALIZED_P0["heightInM"] * 100

    def testWrongVersionRaises(self):
        serializedP1 = _cp.deepcopy(self.SERIALIZED_P1)
        serializedP1["___version____"] = 4
        json = _json.dumps(serializedP1)

        with _pt.raises(_ser.SerializationError):
            Person.from_json(json)

    def testWrongVersion0Raises(self):
        serializedP1 = _cp.deepcopy(self.SERIALIZED_P0)
        serializedP1["___version____"] = "2cba32bd-4c8a-49fc-9f0b-a6b312adcf24"
        json = _json.dumps(serializedP1)

        with _pt.raises(_ser.SerializationError):
            Person.from_json(json)

    def testMissingVersion0DoesNotRaise(self):
        serializedP0 = _cp.deepcopy(self.SERIALIZED_P0)
        del serializedP0["__version__"]

        json = _json.dumps(serializedP0)

        Person.fromUpgradableJson(json)

    def testMissingVersionRaises(self):
        serializedP = _cp.deepcopy(self.SERIALIZED_P)
        del serializedP["__version__"]

        json = _json.dumps(serializedP)

        with _pt.raises(_ser.SerializationError):
            Person.fromUpgradableJson(json)

    def testLoadVersion1(self):
        json = _json.dumps(self.SERIALIZED_P1)

        p1 = PersonVersion1.from_json(json)
        p = Person.fromUpgradableJson(json)

        assert p.title is ""
        assert p.lastName == p1.lastName
        assert p.ageInYears == p1.age
        assert p.heightInCm == p1.heightInCm

    def testWrongFormatRaises(self):
        phonyP1 = self.SERIALIZED_P0.copy()
        firstName = phonyP1["firstName"]
        del phonyP1["firstName"]
        phonyP1["first-mohican"] = firstName

        json = _json.dumps(phonyP1)

        with _pt.raises(_ser.SerializationError):
            Person.fromUpgradableJson(json)

