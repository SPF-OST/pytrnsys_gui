__all__ = [
    "UpgradableJsonSchemaMixinVersion0",
    "UpgradableJsonSchemaMixin",
    "SerializationError",
]

import abc as _abc
import dataclasses as _dc
import typing as _tp
import uuid as _uuid
import logging as _log

import dataclasses_jsonschema as _dcj

_S0 = _tp.TypeVar("_S0", bound="UpgradableJsonSchemaMixinVersion0")
_SOther = _tp.TypeVar("_SOther", bound="UpgradableJsonSchemaMixinVersion0")
_T = _tp.TypeVar("_T", bound="UpgradableJsonSchemaMixin")


_logger = _log.getLogger("root")


class SerializationError(ValueError):
    def __init__(self, *args):
        super().__init__(*args)


@_dc.dataclass
class UpgradableJsonSchemaMixinVersion0(_dcj.JsonSchemaMixin):
    @classmethod
    def from_dict(
        cls: _tp.Type[_S0],
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,
    ) -> _S0:
        if "__version__" in data:
            data = data.copy()
            actualVersion = data.pop("__version__")
            expectedVersion = str(cls.getVersion())

            if actualVersion != expectedVersion:
                raise SerializationError(
                    f"Version mismatch: expected {expectedVersion}, got {actualVersion}."
                )

        try:
            deserializedObject = super().from_dict(data, validate, validate_enums)
        except _dcj.ValidationError as e:
            raise SerializationError("Validation failed.") from e

        return _tp.cast(_S0, deserializedObject)

    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        if "__version__" in data:
            raise AssertionError(
                "Serialized object dictionary from dataclasses-json already contained '__version__' key!"
            )
        data["__version__"] = str(self.getVersion())
        return data

    @classmethod
    @_abc.abstractmethod
    def getVersion(cls) -> _uuid.UUID:
        """To be overwritten in subclass. Use
        .. code-block:: python

            import uuid
            print(str(uuid.uuid4()))

        to generate a version and return that version
        as a *constant* like so:

            .. code-block:: python

            def getVersion(cls):
                return uuid.UUID("41280f1d-67f5-4827-a306-4b2d71cba4c2")
        """
        raise NotImplementedError()


@_dc.dataclass
class UpgradableJsonSchemaMixin(UpgradableJsonSchemaMixinVersion0, _abc.ABC):
    @classmethod
    def from_dict(
        cls: _tp.Type[_T],
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,
    ) -> _T:
        if "__version__" not in data:
            raise SerializationError("No '__version__' field found.")

        return super().from_dict(data, validate, validate_enums)

    @classmethod
    def fromUpgradableJson(
        cls: _tp.Type[_T],
        json: str,
    ) -> _T:
        allVersions = cls._getAllVersionsInDecreasingOrder()

        result = cls._tryGetSupersededObjectAndNewerVersions(json, allVersions)

        if not result:
            # We need to do the following to get dataclasses-jsonschema's nice, detailed error message
            try:
                cls.from_json(json)
            except SerializationError:
                raise
            else:
                raise AssertionError("Shouldn't get here.")

        supersededObject: _S0
        supersededObject, newerVersions = result

        for newerVersion in newerVersions:
            _logger.debug(
                "Attempting to convert %s to %s (%s)...",
                supersededObject.getVersion(),
                newerVersion.__name__,
                newerVersion.getVersion(),
            )
            supersededObject = newerVersion.fromSuperseded(supersededObject)
            _logger.debug(
                "Succeeded to convert %s to %s (%s)...",
                supersededObject.getVersion(),
                newerVersion.__name__,
                newerVersion.getVersion(),
            )
        return supersededObject

    @classmethod
    @_abc.abstractmethod
    def getSupersededClass(cls) -> _SOther:
        raise NotImplementedError()

    @classmethod
    @_abc.abstractmethod
    def fromSuperseded(cls: _tp.Type[_T], superseded: _S0) -> _T:
        raise NotImplementedError()

    @classmethod
    def _getAllVersionsInDecreasingOrder(cls) -> _tp.Sequence[_tp.Type[_S0]]:
        currentVersion = cls
        allVersions = [currentVersion]
        isSuperseding = issubclass(currentVersion, UpgradableJsonSchemaMixin)
        while isSuperseding:
            currentVersion = currentVersion.getSupersededClass()
            allVersions.append(currentVersion)
            isSuperseding = issubclass(currentVersion, UpgradableJsonSchemaMixin)

        return allVersions

    @classmethod
    def _tryGetSupersededObjectAndNewerVersions(
        cls, json: str, allVersions: _tp.Sequence[_tp.Type[_S0]]
    ) -> _tp.Optional[_tp.Tuple[_S0, _tp.Sequence[_tp.Type[_SOther]]]]:
        newerVersions = []
        for version in allVersions:
            supersededObject = cls._getDeserializedDataOrNone(json, version)

            if supersededObject:
                _logger.debug(
                    "Loaded %s at version %s", version.__name__, version.getVersion()
                )
                return supersededObject, list(reversed(newerVersions))

            newerVersions.append(version)

        return None

    @classmethod
    def _getDeserializedDataOrNone(
        cls,
        json: str,
        supersededClass: _S0,
    ) -> _tp.Optional[_S0]:
        try:
            deserializedObject = supersededClass.from_json(json)

            return deserializedObject

        except SerializationError:
            return None
