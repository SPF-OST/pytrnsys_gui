import typing as _tp
import abc as _abc
import dataclasses as _dc
import json as _json

import dataclasses_jsonschema as _dcj
from dataclasses_jsonschema import JsonSchemaMixin

_S0 = _tp.TypeVar("_S0", bound="UpgradableJsonSchemaMixinVersion0")
_SOther = _tp.TypeVar("_SOther", bound="UpgradableJsonSchemaMixinVersion0")
_T = _tp.TypeVar("_T", bound="UpgradableJsonSchemaMixin")


@_dc.dataclass
class UpgradableJsonSchemaMixinVersion0(JsonSchemaMixin):
    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "_VERSION"):
            cls._VERSION = 0
            cls.__annotations__["_VERSION"] = int

        super().__init_subclass__(**kwargs)

    @classmethod
    def fromUpgradableJson(cls: _tp.Type[_S0], data: str) -> _S0:
        kvs = _json.loads(data)

        if "_VERSION" in kvs:
            version = kvs["_VERSION"]
            if version != cls._VERSION:
                raise ValueError(f"Version mismatch: expected {cls._VERSION}, got {version}.")

        return cls.from_dict(kvs)


@_dc.dataclass
class UpgradableJsonSchemaMixin(_abc.ABC, UpgradableJsonSchemaMixinVersion0):
    def __init_subclass__(cls, **kwargs):
        if "supersedes" not in kwargs:
            raise ValueError("You must specify the superseded class using the `supersedes` keyword.")

        supersededClass = kwargs.pop("supersedes")
        cls._SUPERSEDED_CLASS = supersededClass
        cls._VERSION = supersededClass._VERSION + 1 if supersededClass else 0
        cls.__annotations__["_VERSION"] = int

        super().__init_subclass__(**kwargs)

    @classmethod
    def fromUpgradableJson(cls: _tp.Type[_T], data: str) -> _T:
        allVersions = cls._getAllVersionsInDecreasingOrder()

        kvs = _json.loads(data)

        result = cls._tryGetSupersededObjectAndNewerVersions(
            kvs,
            allVersions
        )

        if not result:
            if "_VERSION" not in kvs:
                raise ValueError("Could not determine data format version.")

            # We need to do the following to get dataclasses-json's nice, detailed error message
            try:
                cls.from_dict(kvs)
            except _dcj.ValidationError as e:
                raise ValueError from e
            else:
                raise AssertionError("Shouldn't get here.")

        supersededObject, newerVersions = result

        for newerVersion in newerVersions:
            supersededObject = newerVersion._fromSuperseded(supersededObject)

        return supersededObject

    @classmethod
    def _getAllVersionsInDecreasingOrder(cls):
        currentVersion = cls
        allVersions = [currentVersion]
        isSuperseding = hasattr(currentVersion, "_SUPERSEDED_CLASS")
        while isSuperseding:
            currentVersion = currentVersion._SUPERSEDED_CLASS
            allVersions.append(currentVersion)
            isSuperseding = hasattr(currentVersion, "_SUPERSEDED_CLASS")

        return allVersions

    @classmethod
    def _tryGetSupersededObjectAndNewerVersions(cls, kvs, allVersions):
        newerVersions = []
        for version in allVersions:
            supersededObject = cls._getDeserializedDataOrNone(kvs, version)

            if supersededObject:
                return supersededObject, reversed(newerVersions)

            newerVersions.append(version)

        return None

    @classmethod
    def _getDeserializedDataOrNone(cls, kvs, supersededClass):
        try:
            if not cls._doesVersionMatch(kvs, supersededClass):
                return None

            deserializedObject = supersededClass.from_dict(kvs)

            return deserializedObject

        except _dcj.ValidationError:
            return None

    @classmethod
    def _doesVersionMatch(cls, kvs, supersededClass):
        if "_VERSION" not in kvs:
            isInitialVersion = not hasattr(supersededClass, "_SUPERSEDED_CLASS")
            return isInitialVersion

        version = kvs["_VERSION"]

        return version == supersededClass._VERSION

    @classmethod
    @_abc.abstractmethod
    def _fromSuperseded(cls: _tp.Type[_T], superseded: "UpgradableJsonSchemaMixin") -> _T:
        pass
