import abc as _abc
import dataclasses as _dc
import typing as _tp

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser


@_dc.dataclass
class RequiredDecoderFieldsMixin:
    BlockName: str  # NOSONAR  # pylint: disable=invalid-name
    BlockDisplayName: str  # NOSONAR  # pylint: disable=invalid-name


class UpgradableJsonSchemaMixinBase(_ser.UpgradableJsonSchemaMixin, _abc.ABC):
    @classmethod
    def from_dict(  # NOSONAR  # pylint: disable=invalid-name
        cls,
        data: _dcj.JsonDict,
        validate=True,
        validate_enums: bool = True,  # NOSONAR  # pylint: disable=invalid-name
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # NOSONAR  # pylint: disable=invalid-name
    ):
        if not cls.key() in data:
            raise ValueError(f"Not a `{cls.key()}`.", data)

        del data[cls.key()]

        return super().from_dict(data, validate, validate_enums, schema_type)  # type: ignore[misc]

    def to_dict(  # NOSONAR  # pylint: disable=invalid-name
        self,
        omit_none: bool = True,  # NOSONAR  # pylint: disable=invalid-name
        validate: bool = False,  # NOSONAR  # pylint: disable=invalid-name
        validate_enums: bool = True,  # NOSONAR  # pylint: disable=invalid-name
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # NOSONAR  # pylint: disable=invalid-name
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums, schema_type)  # type: ignore[misc]

        assert self.key() not in data, (
            f"Serialized object dictionary from {_ser.UpgradableJsonSchemaMixinVersion0.__name__} "
            f"already contained `{self.key()}` key!"
        )

        data[self.key()] = True
        return data

    @classmethod
    @_abc.abstractmethod
    def key(cls) -> str:
        raise NotImplementedError()


class BlockItemUpgradableJsonSchemaMixin(
    UpgradableJsonSchemaMixinBase, _abc.ABC
):
    @classmethod
    @_tp.override
    def key(cls) -> str:
        return ".__BlockDict__"


class ConnectionItemUpgradableJsonSchemaMixin(
    UpgradableJsonSchemaMixinBase, _abc.ABC
):
    @classmethod
    @_tp.override
    def key(cls) -> str:
        return ".__ConnectionDict__"
